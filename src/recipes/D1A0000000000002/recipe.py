class NXcitation(object):
    def __init__(self, description, doi, endnote, bibtex):
        self.description = description
        self.doi = doi
        self.endnote = endnote
        self.bibtex = bibtex

    def get_bibtex_ref(self):
        return self.bibtex.split(',')[0].split('{')[1]

    def get_first_author(self):
        parts = self.endnote.split('\n')
        for part in parts:
            if part.startswith("%A"):
                return part.replace("%A", "").strip()

    def get_date(self):
        parts = self.endnote.split('\n')
        for part in parts:
            if part.startswith("%D"):
                return part.replace("%D", "").strip()

    def get_description_with_author(self):
        return "{} \\ref{{}}({}, {})".format(self.description,
                                         self.get_bibtex_ref(),
                                         self.get_first_author(),
                                         self.get_date())


class NXcitation_manager(object):
    def __init__(self):
        self.NXcite_list = []

    def add_citation(self, citation):
        self.NXcite_list.append(citation)

    def get_number_of_citations(self):
        return len(self.NXcite_list)

    def get_full_endnote(self):
        return "\n\n".join([cite.endnote for cite in self.NXcite_list])

    def get_full_bibtex(self):
        return "\n".join([cite.bibtex for cite in self.NXcite_list])

    def get_description_with_citations(self):
        return ".  ".join([cite.get_description_with_author() for cite in self.NXcite_list])

    def get_summary(self):
        return "\nDESCRIPTION\n{}\n\nBIBTEX\n{}\n\nENDNOTE\n{}".format(self.get_description_with_citations(),
                                                                   self.get_full_bibtex(),
                                                                   self.get_full_endnote())

    def __str__(self):
        return "This file has {} citations".format(self.get_number_of_citations())


class NXciteVisitor(object):
    def __init__(self):
        self.citation_manager = NXcitation_manager()

    def _visit_NXcite(self, name, obj):
        if "NX_class" in obj.attrs.keys():
            if str(obj.attrs["NX_class"], "utf-8") in ["NXcite"]:
                citation = NXcitation(str(obj['description'][0], "utf-8"),
                                      str(obj['doi'][0], "utf-8"),
                                      str(obj['endnote'][0], "utf-8"),
                                      str(obj['bibtex'][0], "utf-8"))
                self.citation_manager.add_citation(citation)

    def get_citation_manager(self, nx_file, entry):
        nx_file[entry].visititems(self._visit_NXcite)
        return self.citation_manager


class recipe:
    """
        This recipe recursively finds all NXcite classes in the entry and captures the information in them

        By using this feature you can programmatically gather suggested refereneces for
        the publication of the data of the NeXus file (entry) in question. This can give
        credit to the instrument, special devices, algorithms, calibration methods, data
        acquisition, treatment or analysis applications, etc.
    """

    def __init__(self, filedesc, entrypath):
        self.file = filedesc
        self.entry = entrypath
        self.title = "NXcitation information"

    def process(self):
        citation_manager = NXciteVisitor().get_citation_manager(self.file, self.entry)
        if citation_manager is not None:
            if citation_manager.get_number_of_citations() > 0:
                return citation_manager
        raise AssertionError("This file does not contain any NXcite information")
