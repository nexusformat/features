class recipe:

    """
    Recipe to describe if a file uses the cansas Axis format
    """

    def __init__(self, filedesc, entrypath):
        self.file = filedesc
        self.entry = entrypath
        self.title = "NXData with Cansas NeXus Axis"
        self.failure_comments = []

    def visitor(self, name, obj):
        if "NX_class" not in obj.attrs.keys():
            return
        if obj.attrs["NX_class"] not in ["NXdata"]:
            return
        datasets = list(obj.keys())
        attributes = obj.attrs.keys()
        if "signal" not in attributes:
            self.failure_comments.append("%s : Signal attribute should be present in NXdata" % obj.name)
            return
        signal = obj.attrs['signal'][0]
        if signal not in datasets:
            self.failure_comments.append("%s : Signal attribute points to a non-existent dataset (%s)" % (obj.name, signal))
            return
        if "axes" not in attributes:
            self.failure_comments.append("%s : No axes are specified" % (obj.name))
            return
        for axis in obj.attrs['axes']:
            if axis not in datasets + ['.']:
                self.failure_comments.append("%s : Axis attribute points to a non-existent dataset (%s)" % (obj.name, axis))
                return
        datasets.remove(signal)
        for dataset in datasets:
            if dataset+"_indices" not in attributes:
                self.failure_comments.append("%s : Axis dataset has no corresponding _indices attribute (%s)" % (obj.name, dataset))
                return
        self.NXdatas.append(obj)

    def process(self):
        self.NXdatas = []
        self.file[self.entry].visititems(self.visitor)

        if len(self.NXdatas) == 0:
            raise AssertionError('No NXdata with cansas Axis found\n'+'\n'.join(self.failure_comments))
        return self.NXdatas


