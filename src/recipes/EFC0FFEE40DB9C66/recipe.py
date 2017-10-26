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
        self.title = "scan command available"

    def process(self):
        try:
            scan_command = self.file[self.entry + "/scan_command"][0]

        except Exception as e:
            raise Exception("this feature does not validate correctly: {}".format(str(e)))

        # better have custom exceptions
        return {"scan_command": scan_command}
