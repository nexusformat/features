class recipe:
    """
    NXoff_geometry - examples converting between NeXus and OFF files

    Proposed by: matthew.d.jones@stfc.ac.uk
    """

    def __init__(self, filedesc, entrypath):
        """
        Recipes are required to set a descriptive self.title

        :param filedesc: h5py file object of the NeXus/HDF5 file
        :param entrypath: path of the entry containing this feature
        """

        raise Exception("unedited template code found")

        self.file = filedesc
        self.entry = entrypath
        self.title = "NXoff_geometry - examples converting between NeXus and OFF files"

    def process(self):
        """
        Recipes need to implement this method and return information which
        is useful to a user and instructive to a person reading the code.
        See some of the recommended examples for inspriration what to return.

        :return: the essence of the information recorded in this feature
        """

        raise Exception("unedited template code found")

        return []
