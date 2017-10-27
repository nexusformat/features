

def find_class(nx_file, nx_class):
    """
    Find a given NXclass

    """
    hits = []
    if not isinstance(nx_class, list):
        nx_class = [nx_class]
    def visitor(name, obj):
        if "NX_class" in obj.attrs.keys():
            if obj.attrs["NX_class"].decode() in nx_class:
                hits.append((name, obj))

    nx_file.visititems(visitor)
    return hits

REQUIRED_FIELDS = ['photoelectrons_energy', 'detector_sensitivity', 'energy_direction', 'energy_dispersion']

def check_detector(d):
    hit = []
    for f in REQUIRED_FIELDS:
        if f in d.keys():
            hit.append(f)
    return hit

class recipe(object):
    """
    Recipe to validate files with the NXrixs feature

    WIP: just detector parameters at the moment

    """

    def __init__(self, filedesc, entrypath):
        self.file = filedesc
        self.entry = entrypath
        self.title = "NXrixs"

    def process(self):
        hits = dict()
        for en, e in find_class(self.file, 'NXentry'):
            for dn, d in find_class(e, 'NXdetector'):
                h = check_detector(d)
                if h:
                    hits[en + '/' + dn] = h

        if len(hits) == 0:
            raise Exception('No detectors found with any required fields')        
        nh = len(REQUIRED_FIELDS)
        msg = ''
        for d in hits:
            h = hits[d]
            if len(h) != nh:
                msg += 'Detector {} missing fields: only {}\n'.format(d, h)
        if msg:
            raise Exception(msg)

        return hits


