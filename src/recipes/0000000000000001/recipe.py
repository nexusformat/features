def check_nframes(context, nxTomo, item, values, fails):
    frames = nxTomo[item].shape[0];
    if ('nFrames' not in context.keys()) and frames != 1:
        context['nFrames'] = frames
        context['nFrames_item'] = item
    else:
        if frames not in [context['nFrames'], 1]:
            fails.append("'%s' does not have the same number of frames as '%s'" % (item, context['nFrames_item']))


def include_data(context, nxTomo, item, values, fails):
    values[item] = nxTomo[item];


def check_image_keys(context, nxTomo, item, values, fails):
    data = nxTomo[item][...]
    if data.max() > 3 or data.min() < 0:
        fails.append("'%s' has values outside of the normal range 0 to 3" % (item))


INCLUDE_DATA = 'include_data'
CHECK_NFRAMES = 'check_nframes'
CHECK_IMAGE_KEYS = 'check_image_keys'
VALIDATE = {
    "control": [],
    "control/data": [check_nframes],
    "data": [],
    "data/image_key": [include_data, check_image_keys],
    "data/rotation_angle": [include_data, check_nframes],
    "data/data": [include_data, check_nframes],
    "definition": [],
    "instrument": [],
    "instrument/detector": [],
    "instrument/detector/data": [check_nframes],
    "instrument/detector/distance": [],
    "instrument/detector/image_key": [check_nframes, check_image_keys],
    "instrument/detector/x_pixel_size": [],
    "instrument/detector/y_pixel_size": [],
    "instrument/detector/x_rotation_axis_pixel_position": [],
    "instrument/detector/y_rotation_axis_pixel_position": [],
    "instrument/source": [],
    "instrument/source/current": [],
    "instrument/source/energy": [],
    "instrument/source/name": [],
    "instrument/source/probe": [],
    "instrument/source/type": [],
    "sample": [],
    "sample/name": [],
    "sample/rotation_angle": [check_nframes],
    "sample/x_translation": [check_nframes],
    "sample/y_translation": [check_nframes],
    "sample/z_translation": [check_nframes],
    "title": [],
    "start_time": [],
    "end_time": [],
}


class _NXTomoFinder(object):
    def __init__(self):
        self.hits = []

    def _visit_NXtomo(self, name, obj):
        if "NX_class" in obj.attrs.keys():
            if obj.attrs["NX_class"] in ["NXentry", "NXsubentry"]:
                if "definition" in obj.keys():
                    if obj["definition"][0] == "NXtomo":
                        self.hits.append(obj)

    def get_NXtomo(self, nx_file, entry):
        self.hits = []
        nx_file[entry].visititems(self._visit_NXtomo)
        return self.hits


def check_path(entry, path):
    section = entry
    for part in path.split('/'):
        if part in section.keys():
            section = section[part]
        else:
            return False
    return True


def validate(nxTomo):
    context = {}
    values = {}
    fails = []

    for item in VALIDATE.keys():
        if check_path(nxTomo, item):
            for test in VALIDATE[item]:
                test(context, nxTomo, item, values, fails)
        else:
            fails.append("'NXtomo/%s' is missing from the NXtomo entry" % (item))
    if len(fails) > 0:
        raise AssertionError('\n'.join(fails))
    return values


class recipe:
    """
        This is meant to help consumers of this feature to understand how to implement
        code that understands that feature (copy and paste of the code is allowed).
        It also documents in what preference order (if any) certain things are evaluated
        when finding the information.
    """

    def __init__(self, filedesc, entrypath):
        self.file = filedesc
        self.entry = entrypath
        self.title = "NXtomo"

    def process(self):
        nxTomo = _NXTomoFinder()
        nxTomoList = nxTomo.get_NXtomo(self.file, self.entry)
        if len(nxTomoList) == 0:
            raise AssertionError("No NXtomo entries in this entry")
        entries = []
        failures = []
        for NXtomoEntry in nxTomoList:
            entries.append(validate(NXtomoEntry))
        return entries
