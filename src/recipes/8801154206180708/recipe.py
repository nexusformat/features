class recipe:
    """
    Has experiment_identifier.

    Proposed by: jack.harper@stfc.ac.uk
    """

    def __init__(self, filedesc, entrypath):
        """
        :param filedesc: h5py file object of the NeXus/HDF5 file
        :param entrypath: path of the entry containing this feature
        """
        self.file = filedesc
        self.entry = entrypath
        self.title = "Has experiment_identifier"

    def process(self):
        """
        Finds the experiment identifier.

        :return: the experiment identifier
        :raises: AssertionError if field not found
        """
        try:
            return self.file[self.entry]['experiment_identifier'][0]
        except:
            raise AssertionError("This file does not contain an experiment_identfier field")
