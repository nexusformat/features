class recipe:
    """
    Has event data.

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
        self.event_data_count = 0

    def _has_event_data(self, name, obj):
        if "NX_class" not in obj.attrs.keys():
            return
        if obj.attrs["NX_class"] not in ["NXevent_data"]:
            return
        self.event_data_count += 1

    def process(self):
        """
        Finds the event data.

        :return: the number of the NXevent_data
        :raises: AssertionError if field not found
        """
        self.file[self.entry].visititems(self._has_event_data)
        if self.event_data_count == 0:
            raise AssertionError("This file does not contain an NXevent_data")


if __name__ == '__main__':
    import sys.argv as argv
    import h5py
    recipe(argv[1], argv[2]).process()
