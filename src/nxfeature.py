#! /usr/bin/env python

import h5py
import numpy
import importlib
import sys
import os
from SuperRecipe import SuperRecipe

RECIPIE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/recipes"
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
        r = featuremodule.recipe(self.nxsfile, self.entrypath)
        if isinstance(r, SuperRecipe):
            return r.process()
        else:
            raise Exception(
                "Recipe for feature ID " + str(featureid) + " does not have the correct interface for a recipe")

    def feature_title(self, featureid):
        featuremodule = importlib.import_module("%016X.recipe" % featureid)
        r = featuremodule.recipe(self.nxsfile, self.entrypath)
        return r.title


class FeatureDiscoverer:
    def __init__(self, nxsfile, test_all):
        self.file = h5py.File(nxsfile, 'r')
        self.test_all = test_all

    def entries(self):
        ent = []
        path = RECIPIE_DIR
        for entry in self.file.keys():
            if self.test_all:
                features = [int(feature, 16) for feature in os.listdir(RECIPIE_DIR)]
            else:
                path = "/%s/features" % entry
                features = self.file[path]
                if features.dtype != numpy.dtype("uint64"):
                    # Directory name not of correct form to be a feature, ignore and move on to next
                    continue

            try:
                ent.append(InsaneEntryWithFeatures(self.file, entry, features))
            except:
                print "no recipes in " + path
                pass
        return ent


if __name__ == '__main__':
    import optparse

    usage = "%prog [options] nxs_file"
    parser = optparse.OptionParser(usage=usage)
    parser.add_option("-t", "--test", dest="test", help="Test file against all recipes", action="store_true",
                      default=False)

    (options, args) = parser.parse_args()

    disco = FeatureDiscoverer(args[0], options.test)

    for entry in disco.entries():
        fail_list = []
        error_list = []

        print("Entry \"%s\" appears to contain the following features (they validate correctly): " % entry.entrypath)
        for feat in entry.features():
            try:
                response = entry.feature_response(feat)
                print("\t%s (%d) %s" % (entry.feature_title(feat), feat, response))
            except AssertionError as ae:
                fail_list.append((feat, ae.message))
            except Exception as e:
                fail_list.append((feat, "Undefined validation error:(%s)" % e.message))

        if len(fail_list) > 0:
            print("\nThe following features failed to validate:")
            for feat, message in fail_list:
                try:
                    print("\t%s (%d) is invalid with the following errors:" % (entry.feature_title(feat), feat))
                    print("\t\t" + message.replace('\n', '\n\t\t'))
                except:
                    error_list.append(feat)

        if len(error_list) > 0:
            print("\nThe following features had unexpected errors (Are you running windows?):")
            for feat in error_list:
                print("  (%d)" % (feat))
        print("\n")
