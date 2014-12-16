#! /usr/bin/env python

import h5py, numpy
import importlib, sys, os

# print "%016X" % int("C0FFEEBEEFC0FFEE", 16)
# feature = "C0FFEEBEEFC0FFEE"

RECIPIE_DIR = os.path.dirname(os.path.realpath(__file__))+"/recipes"
sys.path.append(RECIPIE_DIR)

class InsaneEntryWithFeatures:
	def __init__(self, nxsfile, entrypath, featurearray):
		self.nxsfile = nxsfile
		self.entrypath = entrypath
		self.featurearray = featurearray

	def features(self):
		return self.featurearray
		
	def feature_response(self, featureid):
		featuremodule = importlib.import_module("%016X.recipe" % featureid)
		r = featuremodule.recipe(self.nxsfile,self.entrypath)
		return r.process()

	def feature_title(self, featureid):
		featuremodule = importlib.import_module("%016X.recipe" % featureid)
		r = featuremodule.recipe(self.nxsfile,self.entrypath)
		return r.title

class InsaneFeatureDiscoverer:
	def __init__(self, nxsfile):
		self.file = h5py.File(nxsfile, 'r')

	def entries(self):
		ent = []
		for entry in self.file.keys():
			path = "/%s/features" % entry
			try:
				features = self.file[path]
				if features.dtype == numpy.dtype("uint64"):
					ent.append(InsaneEntryWithFeatures(self.file, entry, features))
			except:
				print "no features in "+path
				pass
		return ent

class AllFeatureDiscoverer:
	def __init__(self, nxsfile):
		self.file = h5py.File(nxsfile, 'r')

	def entries(self):
		ent = []
		for entry in self.file.keys():
			try:
				features = [int(feat, 16) for feat in os.listdir(RECIPIE_DIR)]
				ent.append(InsaneEntryWithFeatures(self.file, entry, features))
			except:
				print "no recipies in "+RECIPIE_DIR
				pass
		return ent
		
if __name__ == '__main__':
	import optparse
	usage = "%prog [options] nxs_file"
	parser = optparse.OptionParser(usage=usage)
	parser.add_option("-t", "--test", dest="test", help="Test file against all recipies", action="store_true", default=False)
	
	(options, args) = parser.parse_args()
	
	if options.test:
		disco = AllFeatureDiscoverer(args[0])
	else:
		disco = InsaneFeatureDiscoverer(args[0])
	
	for entry in disco.entries():
		fail_list = []
		error_list = []
		
		print("Entry \"%s\" appears to contain the following features (they validate correctly): " % entry.entrypath)
		for feat in entry.features():
			try:
				response = entry.feature_response(feat)
				print("\t%s (%d) %s" % (entry.feature_title(feat), feat, response))
			except:
				fail_list.append(feat)
	
		if len(fail_list) > 0:
			print("\nThe following features failed to validate:")
			for feat in fail_list:
				try:
					print("\t%s (%d)" % (entry.feature_title(feat), feat))
				except:
					error_list.append(feat)
		
		if len(error_list) > 0:
			print("\nThe following features had unexpected errors (Are you running windows?):")
			for feat in error_list:
				print("  (%d)" % (feat))
		print("\n")
