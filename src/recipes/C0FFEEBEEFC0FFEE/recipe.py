#

class recipe:
	def __init__(self, filedesc, entrypath):
		self.file = filedesc
		self.entry = entrypath

	def process(self):
		return self.entry
	
