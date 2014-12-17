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
		self.title = "NXtomo"

	def extract(self, nxTomo):
		extracted = {"NXtomo":nxTomo}
		failures = []
		for item in ['title', 'start_time', 'end_time', 'definition']:
			if item in nxTomo.keys():
				extracted[item] = nxTomo[item]
			else :
				failures.append("'%s' is missing from the NXtomo entry" % (item))
		
		# Check control
		if "control" in nxTomo.keys():
			control = nxTomo['control']
		else :
			failures.append("NXMonitor control is missing from the NXtomo entry")
		
		return (extracted, failures)

	def process(self):
		nxTomo = _NXTomoFinder()
		nxTomoList = nxTomo.get_NXtomo(self.file, self.entry)
		if len(nxTomoList) == 0:
			 raise AssertionError("No NXtomo entries in this entry")
		entries = []
		failures = []
		for NXtomoEntry in nxTomoList:
			entry, failure = self.extract(NXtomoEntry)
			entries.append(entry)
			failures += failure
		if len(failures) > 0:
			raise AssertionError('\n'.join(failures))
		return entries
