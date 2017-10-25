class recipe:
    """
        A demo recipe for finding the information associated with this demo feature.

        This is meant to help consumers of this feature to understand how to implement
        code that understands that feature (copy and paste of the code is allowed).
        It also documents in what preference order (if any) certain things are evaluated
        when finding the information.
    """

    def __init__(self, filedesc, entrypath):
        self.file = filedesc
        self.entry = entrypath
        self.title = "CIF-style sample geometry"

    def findNXsample(self):
        for node in self.file[self.entry].keys():
            try:
                absnode = "%s/%s" % (self.entry, node)
                if str(self.file[absnode].attrs["NX_class"], 'utf8') == "NXsample":
                    return absnode
            except:
                pass
        # better have custom exceptions
        raise Exception("no NXsample found")

    def process(self):
        dependency_chain = []
        try:
            sample = self.findNXsample()
            depends_on = str(self.file[sample + "/depends_on"][0], 'utf8')
            while not depends_on == ".":
                dependency_chain.append(depends_on)
                depends_on = str(self.file[depends_on].attrs["depends_on"], 'utf8')

        except Exception as e:
            raise Exception("this feature does not validate correctly")

        # better have custom exceptions
        return {"dependency_chain": dependency_chain}
