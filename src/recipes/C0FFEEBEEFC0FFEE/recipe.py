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
                if self.file[absnode].attrs["NX_class"] == "NXsample":
                    return absnode
            except:
                pass
        # better have custom exceptions
        raise Exception("no NXsample found")

    def process(self):
        dependency_chain = []
        try:
            sample = self.findNXsample()
            # this may need more attention for reading all possible types of string
            depends_on = self.file[sample + "/depends_on"][0]
            while not depends_on == ".":
                dependency_chain.append(depends_on)
                # this may need more attention for reading all possible types of string
                depends_on = self.file[depends_on].attrs["depends_on"]

        except Exception as e:
            raise Exception("this feature does not validate correctly: " + e)

        # better have custom exceptions
        return {"dependency_chain": dependency_chain}
