def _visit_gda_scan_command(name, obj):
	if "scan_command" in obj.name:
		return obj[0]

def get_gda_scan_command(nx_file, entry):
	return nx_file[entry].visititems(_visit_gda_scan_command)

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
		self.title = "GDA scan command"

	def process(self):
		gda_scan = get_gda_scan_command(self.file, self.entry)
		if gda_scan is not None:
			return {"GDA scan command" : gda_scan}
		raise Exception("This feature does not validate correctly")