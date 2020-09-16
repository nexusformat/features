#! /usr/bin/env python

import h5py
import numpy
import importlib
import sys
import os

RECIPE_DIR = os.path.dirname(os.path.realpath(__file__)) + "/recipes"
sys.path.append(RECIPE_DIR)


class TestBody:
    def __init__(self, failure_type="", failure_message=""):
        self.failure = failure_type
        self.message = failure_message

    def get_str(self):
        return "\n\t\t\t<failure type=\"{}\">{}</failure>".format(self.failure, self.message) if (self.failure and self.message) else "\n"


class TestCase:
    def __init__(self, class_name, name, body=TestBody()):
        self.class_name = class_name
        self.name = name
        self.body = body

    def get_str(self):
        return "\t\t<testcase classname=\"{}\" name=\"{}\">{}\n\t\t</testcase>".format(self.class_name, self.name, self.body.get_str())


class JUnitFactory:
    def __init__(self):
        self.test_cases = []

    def write(self, xml_file):
        output_str = "<testsuites>\n\t<testsuite name=\"features\" tests=\"" + str(len(self.test_cases)) + "\">\n"
        for test in self.test_cases:
            output_str += test.get_str() + "\n"
        output_str += "\t</testsuite>\n</testsuites>"
        with open(xml_file, "w+") as file:
            file.write(output_str)

    def add_test_case(self, feat, message, failure_type=None, failure_message=None):
        self.test_cases.append(TestCase(feat, message, TestBody(failure_type, failure_message)))


class InsaneEntryWithFeatures:
    def __init__(self, nxsfile, entrypath, featurearray):
        self.nxsfile = nxsfile
        self.entrypath = entrypath
        self.featurearray = featurearray

    def features(self):
        return self.featurearray

    def feature_response(self, featureid):
        featuremodule = importlib.import_module("{:0>16X}.recipe".format(featureid))
        r = featuremodule.recipe(self.nxsfile, self.entrypath)
        return r.process()

    def feature_title(self, featureid):
        featuremodule = importlib.import_module("{:0>16X}.recipe".format(featureid))
        r = featuremodule.recipe(self.nxsfile, self.entrypath)
        return r.title


class InsaneFeatureDiscoverer:
    def __init__(self, nxsfile):
        self.file = h5py.File(nxsfile, 'r')

    def entries(self):
        ent = []
        for entry in self.file.keys():
            path = "/{}/features".format(entry)
            try:
                features = self.file[path]
                if features.dtype == numpy.dtype("uint64"):
                    ent.append(InsaneEntryWithFeatures(self.file, entry, features))
            except:
                print("No features in {}".format(path))
        return ent


class AllFeatureDiscoverer:
    def __init__(self, nxsfile):
        self.file = h5py.File(nxsfile, 'r')

    def entries(self):
        ent = []
        for entry in self.file.keys():
            try:
                features = []
                for feat in os.listdir(RECIPE_DIR):
                    try:
                        features.append(int(feat, 16))
                    except:
                        print("Could not parse feature with name {}".format(feat))
                ent.append(InsaneEntryWithFeatures(self.file, entry, features))
            except:
                print("No features in {}".format(RECIPE_DIR))
        return ent


class SingleFeatureDiscoverer:
    def __init__(self, nxsfile, feature):
        self.file = h5py.File(nxsfile, 'r')
        self.feature = feature

    def entries(self):
        ent = []
        for entry in self.file.keys():
            try:
                ent.append(InsaneEntryWithFeatures(self.file, entry, [self.feature]))
            except:
                print("Issues with parsing feature {}".format(self.feature))
        return ent


if __name__ == '__main__':

    if sys.version_info < (3,0,0):
        print(__file__ + ' requires Python 3. Refusing to run under version ' + str(sys.version[0]) + '.')
        sys.exit(1)

    import argparse
    import traceback

    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--test", dest="test", help="Test file against all recipes", action="store_true",
                        default=False)
    parser.add_argument("-f", "--feature", dest="feature", help="Test file against a defined feature",
                      default=None)
    parser.add_argument("-v", "--verbose", dest="verbose", help="Include full stacktraces of failures", action="store_true",
                        default=False)
    parser.add_argument("-x", "--xml", dest="xml", help="XML file to write the junit output to", default=None)
    parser.add_argument("nexusfile", help="Nexus file to test", nargs='*')

    args = parser.parse_args()

    failed = False
    for file in args.nexusfile:
        if args.feature:
            try:
                disco = SingleFeatureDiscoverer(file, int(args.feature, 16))
            except:
                print("The feature '{}' has not parsed correctly, exiting".format(args.feature))
                sys.exit()
        else:
            if args.test:
                disco = AllFeatureDiscoverer(file)
            else:
                disco = InsaneFeatureDiscoverer(file)

        factory = JUnitFactory()

        for entry in disco.entries():
            pass_list = []
            fail_list = []

            print("Investigating features in {}[{}]".format(file, entry.entrypath))
            for feat in entry.features():
                try:
                    response = entry.feature_response(feat)
                    pass_list.append((feat, response))
                except AssertionError as ae:
                    fail_list.append((feat, type(ae).__name__, str(ae), None))
                except Exception as e:
                    fail_list.append((feat, type(e).__name__, str(e), str(traceback.format_exc())))

            output = str()

            if len(pass_list) > 0:
                print("\tThe following features are contained in this entry:")
                for feat, message in pass_list:
                    print("\t\t{} '{:0>16X}'({}) {}".format(entry.feature_title(feat), feat, feat, message))
                    factory.add_test_case(feat, message)

            if len(fail_list) > 0:
                failed = True
                print("\tThe following features are NOT contained in this entry:")
                for feat, error_type, message, stack in fail_list:
                    try:
                        print("\t\t{} '{:0>16X}'({}) is invalid with the following errors:".format(entry.feature_title(feat), feat, feat))
                        print("\t\t\t{}".format(message.replace('\n', '\n\t\t\t')))
                        if args.verbose and stack:
                            print("\t\t\t{}".format(stack.replace('\n', '\n\t\t\t')))
                        factory.add_test_case(entry.feature_title(feat), feat, error_type, message)
                    except:
                        if args.verbose:
                            print("\t\tFeature ({}) could not be found".format(feat))
            print("\n")
        if args.xml:
            factory.write(args.xml)

    # to fail on Travis, return non zero if fails
    sys.exit(int(failed))
