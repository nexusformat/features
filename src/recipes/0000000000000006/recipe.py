class check_dtype(object):
    """
    A class to check whether the dataset data type matches the expected

    """

    def __init__(self, dtype):
        self.dtype = dtype

    def __call__(self, dset):
        dtype = dset.dtype
        if dtype not in self.dtype:
            return False, "{} is type {}, expected {}".format(
                dset.name, dtype, ', '.join(self.dtype))
        return True, ""


class check_dims(object):
    """
    A class to check whether the dataset dimensions matches the expected

    """

    def __init__(self, dims):
        self.dims = dims

    def __call__(self, dset):
        dims = len(dset.shape)
        if not dims == self.dims:
            return False, '{} has dims {}, expected {}'.format(
                dset.name, str(dims), str(self.dims))
        return True, ''


class check_shape(object):
    """
    A class to check whether the dataset shape matches the expected

    """

    def __init__(self, shape):
        self.shape = shape

    def __call__(self, dset):
        shape = dset.shape
        if not shape == self.shape:
            return False, '{} has shape {}, expected {}'.format(
                dset.name, str(shape), str(self.shape))
        return True, ''


class check_is_scalar(object):
    """
    A class to check whether the dataset is scalar or not

    """

    def __init__(self, is_scalar):
        self.is_scalar = is_scalar

    def __call__(self, dset):
        try:
            data = dset[()]
            s = True
        except Exception:
            s = False
        if s != self.is_scalar:
            return False, '{} == scalar is {}, expected {}'.format(
                dset.name, s, self.is_scalar)
        return True, ''


class check_dset(object):
    """
    Check properties of a dataset

    """

    def __init__(self,
                 dtype=None,
                 dims=None,
                 shape=None,
                 is_scalar=None):
        """
        Set stuff to check
        :param dtype:         The datatype
        :param dims:          The number of dimensions
        :param shape:         The shape of the dataset

        """
        self.checks = []
        if dtype is not None:
            if not isinstance(dtype, list) and not isinstance(dtype, tuple):
                dtype = [dtype]
            self.checks.append(check_dtype(dtype))
        if dims is not None:
            self.checks.append(check_dims(dims))
        if shape is not None:
            self.checks.append(check_shape(shape))
        if is_scalar is not None:
            self.checks.append(check_is_scalar(is_scalar))

    def __call__(self, dset):
        for check in self.checks:
            passed, errors = check(dset)
            if not passed:
                raise RuntimeError(errors)


class check_attr(object):
    """
    Check some properties of an attribute

    """

    def __init__(self, name, value=None, dtype=None):
        """
        Set stuff to check
        :param name:  The name of the attribute
        :param value: The value of the attribute
        :param tests: A list of tests to run

        """
        self.name = name
        self.value = value
        self.dtype = dtype

    def __call__(self, dset):
        if self.name not in dset.attrs.keys():
            raise RuntimeError("'{}' does not have an attribute '{}'".format(
                dset.name, self.name))
        elif self.value is not None and dset.attrs[self.name] != self.value:
            raise RuntimeError("attribute '{}' of {} has value {}, expected {}".format(
                self.name, dset.name, dset.attrs[self.name], self.value))
        elif self.dtype is not None:
            dtype = type(dset.attrs[self.name])
            if not isinstance(dset.attrs[self.name], self.dtype):
                raise RuntimeError("attribute '{}' of '{}' has type {}, expected {}".format(
                    self.name, dset.name, dtype, self.dtype))


def find_entries(nx_file, entry):
    """
    Find NXmx entries

    """
    hits = []

    def visitor(name, obj):
        if "NX_class" in obj.attrs.keys():
            if str(obj.attrs["NX_class"], 'utf8') in ["NXentry", "NXsubentry"]:
                if "definition" in obj.keys():
                    if str(obj["definition"][()], 'utf8') == "NXmx":
                        hits.append(obj)

    visitor(entry, nx_file[entry])
    nx_file[entry].visititems(visitor)
    return hits


def find_class(nx_file, nx_class):
    """
    Find a given NXclass

    """
    hits = []

    def visitor(name, obj):
        if "NX_class" in obj.attrs.keys():
            if str(obj.attrs["NX_class"], 'utf8') == nx_class:
                hits.append(obj)

    nx_file.visititems(visitor)
    return hits


def convert_units(value, input_units, output_units):
    """
    Hacky utility function to convert units

    """
    converters = {
        'm': {
            'mm': lambda x: x * 1e3,
            'microns': lambda x: x * 1e6,
            'nm': lambda x: x * 1e9
        },
        'mm': {
            'm': lambda x: x * 1e-3,
            'microns': lambda x: x * 1e3,
            'nm': lambda x: x * 1e6
        },
        'microns': {
            'm': lambda x: x * 1e-6,
            'mm': lambda x: x * 1e-3,
            'nm': lambda x: x * 1e3
        },
        'nm': {
            'm': lambda x: x * 1e-9,
            'mm': lambda x: x * 1e-6,
            'microns': lambda x: x * 1e-3,
            'angstroms': lambda x: x * 10
        }
    }
    if input_units == output_units:
        return value
    try:
        return converters[input_units][output_units](value)
    except Exception:
        pass
    raise RuntimeError('Can\'t convert units "{}" to "{}"'.format(input_units, output_units))


def visit_dependencies(nx_file, item, visitor=None):
    """
    Walk the dependency chain and call a visitor function

    """
    import os.path
    dependency_chain = []
    if os.path.basename(item) == 'depends_on':
        depends_on = nx_file[item][()]
    else:
        depends_on = nx_file[item].attrs['depends_on']
    while not depends_on == ".":
        if visitor is not None:
            visitor(nx_file, depends_on)
        if depends_on in dependency_chain:
            raise RuntimeError("'{}' is a circular dependency".format(depends_on))
        try:
            item = nx_file[depends_on]
        except Exception:
            raise RuntimeError("'{}' is missing from nx_file".format(depends_on))
        dependency_chain.append(depends_on)
        try:
            depends_on = nx_file[depends_on].attrs["depends_on"]
        except Exception:
            raise RuntimeError("'{}' contains no depends_on attribute".format(depends_on))


def construct_vector(nx_file, item, vector=None):
    """
    Walk the dependency chain and create the absolute vector

    """
    from scitbx import matrix

    class TransformVisitor(object):
        def __init__(self, vector):
            self.vector = matrix.col(vector)

        def __call__(self, nx_file, depends_on):
            from scitbx import matrix
            item = nx_file[depends_on]
            value = item[()]
            units = str(item.attrs['units'], 'utf8')
            ttype = str(item.attrs['transformation_type'], 'utf8')
            vector = matrix.col(item.attrs['vector'])
            if ttype == 'translation':
                value = convert_units(value, units, 'mm')
                self.vector = vector * value + self.vector
            elif ttype == 'rotation':
                if units == 'rad':
                    deg = False
                elif units == 'deg':
                    deg = True
                else:
                    raise RuntimeError('Invalid units: {}'.format(units))
                self.vector.rotate(axis=vector, angle=value, deg=deg)
            else:
                raise RuntimeError('Unknown transformation_type: {}'.format(ttype))

        def result(self):
            return self.vector

    if vector is None:
        value = nx_file[item][()]
        units = str(nx_file[item].attrs['units'], 'uft8')
        ttype = str(nx_file[item].attrs['transformation_type'], 'uft8')
        vector = nx_file[item].attrs['vector']
        if ttype == 'translation':
            value = convert_units(value, units, "mm")
            vector = vector * value
    else:
        pass
    visitor = TransformVisitor(vector)

    visit_dependencies(nx_file, item, visitor)

    return visitor.result()


def run_checks(handle, items):
    """
    Run checks for datasets

    """
    for item, detail in items.items():
        min_occurs = detail["minOccurs"]
        checks = detail['checks']
        assert (min_occurs in [0, 1])
        try:
            dset = handle[item]
        except Exception:
            dset = None
            if min_occurs != 0:
                raise RuntimeError('Could not find {} in {}'.format(item, handle.name))
            else:
                continue
        if dset is not None:
            for check in checks:
                check(dset)


class NXdetector_module(object):
    """
    A class to hold a handle to NXdetector_module

    """

    def __init__(self, handle, errors=None):
        self.handle = handle

        items = {
            "data_origin": {
                "minOccurs": 1,
                "checks": [
                    check_dset(dtype=["uint32", "uint64", "int32", "int64"], shape=(2,))
                ]
            },
            "data_size": {
                "minOccurs": 1,
                "checks": [
                    check_dset(dtype=["int32", "int64", "uint32", "uint64"], shape=(2,))
                ]
            },
            "module_offset": {
                "minOccurs": 1,
                "checks": [
                    check_dset(dtype=["float64", "float32", "int64", "int32"], is_scalar=True),
                    check_attr("transformation_type"),
                    check_attr("vector"),
                    check_attr("offset"),
                    check_attr("units", dtype=bytes),
                    check_attr("depends_on")
                ]
            },
            "fast_pixel_direction": {
                "minOccurs": 1,
                "checks": [
                    check_dset(dtype=["float32", "float64"], is_scalar=True),
                    check_attr("transformation_type"),
                    check_attr("vector"),
                    check_attr("offset"),
                    check_attr("units", dtype=bytes),
                    check_attr("depends_on")
                ]
            },
            "slow_pixel_direction": {
                "minOccurs": 1,
                "checks": [
                    check_dset(dtype=["float32", "float64"], is_scalar=True),
                    check_attr("transformation_type"),
                    check_attr("vector"),
                    check_attr("offset"),
                    check_attr("units", dtype=bytes),
                    check_attr("depends_on"),
                ]
            },
        }

        run_checks(self.handle, items)


class NXdetector(object):
    """
    A class to handle a handle to NXdetector

    """

    def __init__(self, handle, errors=None):

        self.handle = handle

        # The items to validate
        items = {
            "depends_on": {
                "minOccurs": 1,
                "checks": []
            },
            "data": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dims=3)
                ]
            },
            "description": {
                "minOccurs": 1,
                "checks": []
            },
            "time_per_channel": {
                "minOccurs": 0,
                "checks": []
            },
            "distance": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=["float32", "float64"], is_scalar=True)
                ]
            },
            "dead_time": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=["float32", "float64"], is_scalar=True)
                ]
            },
            "count_time": {
                "minOccurs": 1,
                "checks": [
                    check_dset(dtype=["float32", "float64"], is_scalar=True)
                ]
            },
            "beam_centre_x": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=["float32", "float64"], is_scalar=True)
                ]
            },
            "beam_centre_y": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=["float32", "float64"], is_scalar=True)
                ]
            },
            "angular_calibration_applied": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=['int32', 'int64', 'uint32', 'uint64'], is_scalar=True)
                ]
            },
            "angular_calibration": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=["float32", "float64"])
                ]
            },
            "flatfield_applied": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=['int32', 'int64', 'uint32', 'uint64'], is_scalar=True)
                ]
            },
            "flatfield": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=["float32", "float64"])
                ]
            },
            "flatfield_error": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=["float32", "float64"])
                ]
            },
            "pixel_mask_applied": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=['int32', 'int64', 'uint32', 'uint64'], is_scalar=True)
                ]
            },
            "pixel_mask": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype="int32")
                ]
            },
            "countrate_correction_applied": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=['int32', 'int64', 'uint32', 'uint64'], is_scalar=True)
                ]
            },
            "bit_depth_readout": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=['int32', "int64"], is_scalar=True)
                ]
            },
            "detector_readout_time": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=['float32', "float64"], is_scalar=True)
                ]
            },
            "frame_time": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=['float32', "float64"], is_scalar=True)
                ]
            },
            "gain_setting": {
                "minOccurs": 0,
                "checks": []
            },
            "saturation_value": {
                "minOccurs": 1,
                "checks": [
                    check_dset(dtype=["int32", "int64"], is_scalar=True)
                ]
            },
            "sensor_material": {
                "minOccurs": 1,
                "checks": []
            },
            "sensor_thickness": {
                "minOccurs": 1,
                "checks": [
                    check_dset(dtype=["float32", "float64"], is_scalar=True),
                    check_attr("units", dtype=bytes)
                ]
            },
            "threshold_energy": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=['float32', "float64"], is_scalar=True)
                ]
            },
            "type": {
                "minOccurs": 1,
                "checks": []
            },
        }

        run_checks(self.handle, items)

        # Find the NXdetector_modules
        self.modules = []
        for entry in find_class(self.handle, "NXdetector_module"):
            try:
                self.modules.append(NXdetector_module(entry, errors=errors))
            except Exception as e:
                if errors is not None:
                    errors.append(str(e))

        # Check we've got some stuff
        if len(self.modules) == 0:
            raise RuntimeError('No NXdetector_module in {}'.format(self.handle.name))


class NXinstrument(object):
    """
    A class to hold a handle to NXinstrument

    """

    def __init__(self, handle, errors=None):

        self.handle = handle

        # Find the NXdetector
        self.detectors = []
        for entry in find_class(self.handle, "NXdetector"):
            try:
                self.detectors.append(NXdetector(entry, errors=errors))
            except Exception as e:
                if errors is not None:
                    errors.append(str(e))

        # Check we've got stuff
        if len(self.detectors) == 0:
            raise RuntimeError('No NXdetector in {}'.format(self.handle.name))


class NXbeam(object):
    """
    A class to hold a handle to NXbeam

    """

    def __init__(self, handle, errors=None):
        self.handle = handle

        items = {
            "incident_wavelength": {
                "minOccurs": 1,
                "checks": [
                    check_dset(dtype=['float32', "float64"], is_scalar=True)
                ]
            },
            "incident_wavelength_spectrum": {
                "minOccurs": 0,
                "checks": []
            },
            "incident_polarization_stokes": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=["float32", "float64"], shape=(4,))
                ]
            },
            "flux": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype=["float32", "float64"], is_scalar=True)
                ]
            },
        }

        run_checks(self.handle, items)


class NXsample(object):
    """
    A class to hold a handle to NXsample

    """

    def __init__(self, handle, errors=None):

        self.handle = handle

        items = {
            "name": {
                "minOccurs": 0,
                "checks": []
            },
            "depends_on": {
                "minOccurs": 1,
                "checks": []
            },
            "chemical_formula": {
                "minOccurs": 0,
                "checks": []
            },
            "unit_cell": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype="float64", dims=2)
                ]
            },
            "unit_cell_class": {
                "minOccurs": 0,
                "checks": []
            },
            "unit_cell_group": {
                "minOccurs": 0,
                "checks": []
            },
            "sample_orientation": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype="float64", shape=(3,))
                ]
            },
            "orientation_matrix": {
                "minOccurs": 0,
                "checks": [
                    check_dset(dtype="float64", dims=3)
                ]
            },
            "temperature": {
                "minOccurs": 0,
                "checks": []
            },
        }

        run_checks(self.handle, items)

        # Find the NXsource
        self.beams = []
        for entry in find_class(self.handle, "NXbeam"):
            try:
                self.beams.append(NXbeam(entry, errors=errors))
            except Exception as e:
                if errors is not None:
                    errors.append(str(e))

        # Check we've got stuff
        if len(self.beams) == 0:
            raise RuntimeError('No NXbeam in {}'.format(self.handle.name))


class NXdata(object):
    """
    A class to hold a handle to NXdata

    """

    def __init__(self, handle, errors=None):
        self.handle = handle


class NXmxEntry(object):
    """
    A class to hold a handle to NXmx entries

    """

    def __init__(self, handle, errors=None):

        self.handle = handle

        items = {
            'title': {
                "minOccurs": 0,
                "checks": []
            },
            "start_time": {
                "minOccurs": 0,
                "checks": []
            },
            "end_time": {
                "minOccurs": 0,
                "checks": []
            },
        }

        run_checks(self.handle, items)

        # Find the NXinstrument
        self.instruments = []
        for entry in find_class(self.handle, "NXinstrument"):
            try:
                self.instruments.append(NXinstrument(entry, errors=errors))
            except Exception as e:
                if errors is not None:
                    errors.append(str(e))

        # Find the NXsample
        self.samples = []
        for entry in find_class(self.handle, "NXsample"):
            try:
                self.samples.append(NXsample(entry, errors=errors))
            except Exception as e:
                if errors is not None:
                    errors.append(str(e))

        # Find the NXidata
        self.data = []
        for entry in find_class(self.handle, "NXdata"):
            try:
                self.data.append(NXdata(entry, errors=errors))
            except Exception as e:
                if errors is not None:
                    errors.append(str(e))

        # Check we've got some stuff
        if len(self.instruments) == 0:
            raise RuntimeError('No NXinstrument in {}'.format(self.handle.name))
        if len(self.samples) == 0:
            raise RuntimeError('No NXsample in {}'.format(self.handle.name))
        if len(self.data) == 0:
            raise RuntimeError('No NXdata in {}'.format(self.handle.name))


def validate(nx_file, item, test):
    """
    Validate the NXmx entries

    """
    values = []
    fails = []
    context = {}
    test(context, nx_file, item, values, fails)
    if len(fails) > 0:
        raise AssertionError('\n'.join(fails))
    return values


def check_path(nx_file, path):
    """
    Ensure path exists

    """
    section = nx_file
    try:
        nx_file[path]
    except Exception:
        return False
    return True


class recipe:
    """
    Recipe to validate files with the NXmx feature

    """

    def __init__(self, filedesc, entrypath):
        self.file = filedesc
        self.entry = entrypath
        self.title = "NXmx"

    def process(self):
        # A list of errors
        self.errors = []

        # Find the NXmx entries
        self.entries = []
        for entry in find_entries(self.file, "/"):
            try:
                self.entries.append(NXmxEntry(entry, errors=self.errors))
            except Exception as e:
                self.errors.append(str(e))

        # Check we've got some stuff
        if len(self.entries) == 0:
            raise RuntimeError("""
        Error reading NXmxfile: {}
          No NXmx entries in file

        The following errors occurred:

        {}
      """.format(self.file.filename, "\n".join(self.errors)))


if __name__ == '__main__':
    import sys
    import h5py

    handle = h5py.File(sys.argv[1])

    r = recipe(handle, '/')
    r.process()
