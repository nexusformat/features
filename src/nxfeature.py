#! /usr/bin/env python

import h5py, numpy
import importlib, sys, os

# print "%016X" % int("C0FFEEBEEFC0FFEE", 16)
# feature = "C0FFEEBEEFC0FFEE"

sys.path.append(os.path.dirname(os.path.realpath(__file__))+"/recipes")

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
		
if __name__ == '__main__':
	disco = InsaneFeatureDiscoverer(sys.argv[1])
	for entry in disco.entries():
		print "Entry %s has the following features: " % entry.entrypath
		for feat in entry.features():
			print entry.feature_title(feat), "(%d)" % feat, entry.feature_response(feat)

