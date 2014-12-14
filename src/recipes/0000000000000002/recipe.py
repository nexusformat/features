def getNXDetectorWithImageKey(name, obj):
	if "NX_class" in obj.attrs.keys():
		if obj.attrs["NX_class"] in ["NXdetector"]:
			if "image_key" in obj.keys():
				return obj

class recipe:
	"""
		A demo recipe for finding the information associated with this demo feature.
		
		This is meant to help consumers of this feature to understand how to implement 
		code that understands that feature (copy and paste of the code is allowed).
		It also documents in what preference order (if any) certain things are evaluated
		when finding the information.
	"""

	def __init__(self, filedesc, entrypath):
		self.file = filedesc
		self.entry = entrypath
		self.title = "NXdetector with image key"

	def process(self):
		nxDet = self.file[self.entry].visititems(getNXDetectorWithImageKey)
		if nxDet is not None:
			return {"NXdetector with image_key" : nxDet}
		raise Exception("This feature does not validate correctly")