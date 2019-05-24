class recipe:
    """
    Create an OFF file from an NXdisk_chopper

    Proposed by: dolica.akello-egwel@stfc.ac.uk
    Please change this docstring to something meaningful
    that describes your NeXus feature.
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
        self.title = "Create an OFF file from an NXdisk_chopper"

    def process(self):
        """
        Recipes need to implement this method and return information which
        is useful to a user and instructive to a person reading the code.
        See some of the recommended examples for inspiration what to return.

        :return: the essence of the information recorded in this feature
        """

        raise Exception("unedited template code found")

        return []
