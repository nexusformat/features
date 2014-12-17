INCLUDE_DATA = 'include_data'
CHECK_NFRAMES = 'check_nframes'
VALIDATE = {
			"control": [],
			"control/data": [CHECK_NFRAMES], 
			"data":[],
			"data/image_key":[INCLUDE_DATA],
			"data/rotation_angle":[INCLUDE_DATA,CHECK_NFRAMES],
			"data/data":[INCLUDE_DATA,CHECK_NFRAMES],
			"definition":[],
			"instrument":[],
			"instrument/detector":[],
			"instrument/detector/data":[CHECK_NFRAMES],
			"instrument/detector/distance":[],
			"instrument/detector/image_key":[CHECK_NFRAMES],
			"instrument/detector/x_pixel_size":[],
			"instrument/detector/y_pixel_size":[],
			"instrument/detector/x_rotation_axis_pixel_position":[],
			"instrument/detector/y_rotation_axis_pixel_position":[],
			"instrument/source":[],
			"instrument/source/current":[],
			"instrument/source/energy":[],
			"instrument/source/name":[],
			"instrument/source/probe":[],
			"instrument/source/type":[],
			"sample":[],
			"sample/name":[],
			"sample/rotation_angle":[CHECK_NFRAMES],
			"sample/x_translation":[CHECK_NFRAMES],
			"sample/y_translation":[CHECK_NFRAMES],
			"sample/z_translation":[CHECK_NFRAMES],
			"title":[],
			"start_time":[],
			"end_time":[],
			}

class _NXTomoFinder(object):
	def __init__(self):
		self.hits = []

	def _visit_NXtomo(self, name, obj):
		if "NX_class" in obj.attrs.keys():
			if obj.attrs["NX_class"] in ["NXentry", "NXsubentry"]:
				if "definition" in obj.keys():
					if obj["definition"][0] == "NXtomo":
						self.hits.append(obj)
	
	def get_NXtomo(self, nx_file, entry):
		self.hits = []
		nx_file[entry].visititems(self._visit_NXtomo)
		return self.hits

def check_path(entry, path):
	section = entry
	for part in path.split('/'):
		if part in section.keys():
			section = section[part]
		else :
			return False
	return True

def validate(nxTomo):
	values = {}
	fails = []
	nFrames = None
	nFrames_item = ""

	for item in VALIDATE.keys():
		if check_path(nxTomo, item):
			if INCLUDE_DATA in VALIDATE[item]:
				values[item] = nxTomo[item];
			if CHECK_NFRAMES in VALIDATE[item]:
				frames = nxTomo[item].shape[0];
				if nFrames == None and frames != 1:
					nFrames = frames
					nFrames_item = item
				else :
					if not frames in [nFrames, 1]:
						fails.append("'%s' does not have the same number of frames as '%s'" % (item, nFrames_item))					
		else:
			fails.append("'NXtomo/%s' is missing from the NXtomo entry" % (item))
	if len(fails) > 0:
		raise AssertionError('\n'.join(fails))
	return values

class recipe:
	"""
		This is meant to help consumers of this feature to understand how to implement 
		code that understands that feature (copy and paste of the code is allowed).
		It also documents in what preference order (if any) certain things are evaluated
		when finding the information.
	"""

	def __init__(self, filedesc, entrypath):
		self.file = filedesc
		self.entry = entrypath
		self.title = "NXtomo"

	def process(self):
		nxTomo = _NXTomoFinder()
		nxTomoList = nxTomo.get_NXtomo(self.file, self.entry)
		if len(nxTomoList) == 0:
			 raise AssertionError("No NXtomo entries in this entry")
		entries = []
		failures = []
		for NXtomoEntry in nxTomoList:
			entries.append(validate(NXtomoEntry))
		return entries
