def getNXtomo(name, obj):
	if "NX_class" in obj.attrs.keys():
		if obj.attrs["NX_class"] in ["NXentry", "NXsubentry"]:
			if "definition" in obj.keys():
				if obj["definition"][0] == "NXtomo":
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
		self.title = "NXtomo discover"

	def process(self):
		nxTomo = self.file[self.entry].visititems(getNXtomo)
		if nxTomo is not None:
			return {"NXtomo" : nxTomo}
		raise Exception("This feature does not validate correctly")