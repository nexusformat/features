class recipe:
    """
    Has title.

    Proposed by: jack.harper@stfc.ac.uk
    """

    def __init__(self, filedesc, entrypath):
        """
        :param filedesc: h5py file object of the NeXus/HDF5 file
        :param entrypath: path of the entry containing this feature
        """
        self.file = filedesc
        self.entry = entrypath
        self.title = "Has title"

    def process(self):
        """
        Finds the title.

        :return: the title
        :raises: AssertionError if field not found
        """
        try:
            return self.file[self.entry]['title'][0]
        except:
            raise AssertionError("This file does not contain a title field")
