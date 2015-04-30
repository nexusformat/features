
class check_dset(object):
  ''' 
  Check properties of a dataset

  '''

  def __init__(self, 
               dtype=None, 
               dims=None, 
               shape=None, 
               same_shape_as=None, 
               linked=None,
               is_scalar=None):
    '''
    Set stuff to check
    :param dtype:         The datatype
    :param dims:          The number of dimensions
    :param shape:         The shape of the dataset
    :param same_shape_as: A dataset this should match in shape
    :param linked:        A dataset this should be linked to

    '''
    if dtype is not None:
      if not isinstance(dtype, list) and not isinstance(dtype, tuple):
        dtype = [dtype]
    self.dtype = dtype
    self.dims = dims
    self.shape = shape
    self.same_shape_as = same_shape_as
    self.linked = linked
    self.is_scalar = is_scalar

  def __call__(self, context, nx_file, item, values, fails):
    from os.path import isabs, dirname, join, abspath
    try:
      if self.dtype is not None:
        dtype = nx_file[item].dtype
        if not dtype in self.dtype:
          fails.append("'%s' is of type %s, expected %s" % (
            item, dtype, self.dtype))
      if self.dims is not None:
        dims = len(nx_file[item].shape)
        if not dims == self.dims:
          fails.append("'%s' has dims=%d, expected %d" % (
            item, dims, self.dims))
      if self.shape is not None:
        shape = nx_file[item].shape
        if not shape == self.shape:
          fails.append("'%s' has shape=%s, expected %s" % (
            item, str(shape), str(self.shape)))
      if self.same_shape_as is not None:
        if not isabs(self.same_shape_as):
          other = abspath(join(dirname(item), self.same_shape_as))
        else:
          other = abspath(self.same_shape_as)
        shape1 = nx_file[item].shape
        shape2 = nx_file[other].shape
        if not shape1 == shape2:
          fails.append("'%s' does not have same shape as '%s' (%s)" % (
            item, str(shape1), other, str(shape2)))
      if self.is_scalar is not None:
        try:
          data = nx_file[item].value
          s = True
        except Exception:
          s = False
        if s != self.is_scalar:
          fails.append("'%s' is scalar == %s, expected %s" % (item, s, self.is_scalar))
      if self.linked is not None:
        if not isabs(self.linked):
          other = abspath(join(dirname(item), self.linked))
        else:
          other = abspath(self.linked)
        if nx_file[item] != nx_file[other]:
          fails.append("'%s' is not linked to %s" % (item, other))
    except Exception, e:
      raise RuntimeError(
        '''
        Failed in check_dset for "%s"

        %s

        ''' % (item, str(e)))

class check_depends_on(object):
  '''
  Check the dependancy chain to make sure it terminates and doesn't 
  contain loops.

  '''
  def __init__(self):
    pass

  def __call__(self, context, nx_file, item, values, fails):
    dependency_chain = []
    assert(item.count("@") <= 1)
    if item.count("@") == 1:
      item, attr = item.split("@")
      depends_on = nx_file[item].attrs[attr]
    else:
      depends_on = nx_file[item][0]
    nx_file = nx_file.file
    while not depends_on == ".":
      if depends_on in dependency_chain:
        fails.append("'%s' is a circular dependency" % depends_on)
      try:
        item = nx_file[depends_on]
      except Exception, e:
        fails.append("'%s' is missing from nx_file" % depends_on)
        break
      dependency_chain.append(depends_on)
      try:
        depends_on = nx_file[depends_on].attrs["depends_on"]
      except Exception:
        fails.append("'%s' contains no depends_on attribute" % depends_on)
        break

class check_attr(object):
  '''
  Check some properties of an attribute

  '''

  def __init__(self, name, value=None, tests=None):
    '''
    Set stuff to check
    :param name:  The name of the attribute
    :param value: The value of the attribute
    :param tests: A list of tests to run

    '''
    self.name = name
    self.value = value
    self.tests = tests

  def __call__(self, context, nx_file, item, values, fails):
    if not self.name in nx_file[item].attrs.keys():
      fails.append("'%s' does not have an attribute '%s'" % (
        item, self.name))
    elif self.value is not None and nx_file[item].attrs[self.name] != self.value:
      fails.append("attribute '%s' of %s has value %s, expected %s" % (
        self.name, item, nx_file[item].attrs[self.name], self.value))
    if self.tests is not None:
      from os.path import join
      path = item
      for test in self.tests:
        test(context, nx_file, item + "@" + self.name, values, fails)

class check_nx_class(object):
  '''
  Base class to test an NXclass

  '''

  def __call__(self, context, nx_file, item, values, fails):
    from os.path import join
    path = item
    for item, detail in self.items.iteritems():
      min_occurs = detail["minOccurs"]
      tests = detail['tests']
      if "class" in detail:
        instances = self.find(nx_file, item)
        if len(instances) < min_occurs:
          raise AssertionError("No instances of %s found, expected %i" % (item, min_occurs))
        for item in instances:
          self.process(context, nx_file, item.name, 1, tests, values, fails)
      else:
        self.process(context, nx_file, join(path,item), min_occurs, tests, values, fails)
    return values

  def find(self, nx_file, nx_class):
    hits = []
    def visitor(name, obj):
      if "NX_class" in obj.attrs.keys():
        if obj.attrs["NX_class"] in [nx_class]:
          hits.append(obj)
    nx_file.visititems(visitor)
    return hits

  def process(self, context, nx_file, item, min_occurs, tests, values, fails):
    assert(min_occurs in [0, 1])
    if check_path(nx_file, item):
      for test in tests:
        test(context, nx_file, item, values, fails)
    elif min_occurs == 1:
      fails.append("'%s' is missing from the nx file" % (item))

class check_nx_detector_module(check_nx_class):
  '''
  Check the contents of an NXdetector_module

  '''

  def __init__(self):
    from os.path import join

    # The items to validate
    self.items = { 
      "data_origin" : { 
        "minOccurs" : 1, 
        "tests" : [
          check_dset(dtype="int64", shape=(2,))
        ] 
      },
      "data_size" : { 
        "minOccurs" : 1, 
        "tests" : [
          check_dset(dtype="int64", shape=(2,))
        ] 
      },
      "module_offset" : { 
        "minOccurs" : 1, 
        "tests" : [
          check_dset(dtype=["float64", "float32", "int64", "int32"], is_scalar=True), 
          check_attr("transformation_type"), 
          check_attr("vector"), 
          check_attr("offset"),
          check_attr("depends_on", tests=[
            check_depends_on(),
          ])
        ] 
      },
      "fast_pixel_direction" : {
        "minOccurs" : 1, 
        "tests" : [
          check_dset(dtype="float64", is_scalar=True), 
          check_attr("transformation_type"), 
          check_attr("vector"), 
          check_attr("offset"),
          check_attr("depends_on", tests=[
            check_depends_on(),
          ])
        ] 
      },
      "slow_pixel_direction" : {
        "minOccurs" : 1, 
        "tests" : [
          check_dset(dtype="float64", is_scalar=True), 
          check_attr("transformation_type"), 
          check_attr("vector"), 
          check_attr("offset"),
          check_attr("depends_on", tests=[
            check_depends_on(),
          ])
        ] 
      },
    }
    
class check_nx_detector(check_nx_class):
  '''
  Check the contents of an NXdetector

  '''

  def __init__(self):
    from os.path import join
    
    # The items to validate
    self.items = {
      "depends_on" : {
        "minOccurs" : 1,
        "tests" : [
          check_depends_on()
        ]
      },
      "data" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dims=3)
        ]
      },
      "description" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "time_per_channel" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "distance" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
      "dead_time" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
      "count_time" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
      "beam_centre_x" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
      "beam_centre_y" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
      "angular_calibration_applied" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="bool", is_scalar=True)
        ]
      },
      "angular_calibration" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", same_shape_as="data")
        ]
      },
      "flatfield_applied" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="bool", is_scalar=True)
        ]
      },
      "flatfield" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", same_shape_as="data")
        ]
      },
      "flatfield_error" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", same_shape_as="data")
        ]
      },
      "pixel_mask_applied" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="bool", is_scalar=True)
        ]
      },
      "pixel_mask" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="int32", same_shape_as="data")
        ]
      },
      "countrate_correction_applied" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="bool", is_scalar=True)
        ]
      },
      "bit_depth_readout" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="int64", is_scalar=True)
        ]
      },
      "detector_readout_time" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
      "frame_time" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
      "gain_setting" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "saturation_value" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="int64", is_scalar=True)
        ]
      },
      "sensor_material" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "sensor_thickness" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
      "threshold_energy" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
      "type" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "NXdetector_module" : {
        "class" : True,
        "minOccurs" : 1,
        "tests" : [
          check_nx_detector_module(),
        ]
      }
    } 

class check_nx_attenuator(check_nx_class):
  '''
  Check the contents of an NXattenuator

  '''
  
  def __init__(self):
    self.items = {
      "attenuator_transmission" : {
        "minOccurs" : 1,
        "tests" : []
      }
    }

class check_nx_beam(check_nx_class):
  '''
  Check the contents of an NXbeam

  '''

  def __init__(self):
    self.items = {
      "incident_wavelength" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
      "incident_wavelength_spectrum" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "incident_polarization_stokes" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", shape=(4,))  
        ]
      },
      "flux" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", is_scalar=True)
        ]
      },
    }

class check_nx_data(check_nx_class):
  '''
  Check the contents of an NXdata

  '''

  def __init__(self):
    self.items = {
      "data" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype=["float32", "float64", "int32", "int64", "int16"], dims=3)
        ]
      }
    }

class check_nx_sample(check_nx_class):
  '''
  Check the contents of an NXsample

  '''

  def __init__(self):
    self.items = {
      "name" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "depends_on" : {
        "minOccurs" : 1,
        "tests" : [
          check_depends_on()
        ]
      },
      "chemical_formula" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "unit_cell" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", dims=2)
        ]
      },
      "unit_cell_class" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "unit_cell_group" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "sample_orientation" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", shape=(3,))
        ]
      },
      "orientation_matrix" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", dims=3)
        ]
      },
      "temperature" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "transformations" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "NXbeam" : {
        "class" : True,
        "minOccurs" : 1,
        "tests" : [
          check_nx_beam()
        ]
      }
    }

class check_nx_instrument(check_nx_class):
  '''
  Check the contents of an NXinstrument

  '''

  def __init__(self):

    self.items = {
      "NXattenuator" : {
        "class" : True,
        "minOccurs" : 0,
        "tests" : [
          check_nx_attenuator()
        ]
      },
      "NXdetector" : {
        "class" : True,
        "minOccurs" : 1,
        "tests" : [
          check_nx_detector()
        ],
      },
    }

class check_nx_mx(check_nx_class):
  '''
  Check the contents of an NXmn entry

  '''
  
  def __init__(self):

    self.items = {
      'title' : {
        "minOccurs" : 1,
        "tests" : []
      },
      "start_time" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "end_time" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "NXdata" : {
        "class" : True,
        "minOccurs" : 1,
        "tests" : [
          check_nx_data()
        ]
      },
      "instrument" : {
        "minOccurs" : 1,
        "tests" : [
          check_nx_instrument(),
          check_attr("NX_class", "NXinstrument")
        ]
      },
      "NXsample" : {
        "class" : True,
        "minOccurs" : 1,
        "tests" : [
          check_nx_sample(),
        ]
      }
    }

def find_nx_mx_entries(nx_file, entry):
  ''' 
  Find NXmx entries 
  
  '''
  hits = []
  def visitor(name, obj):
    if "NX_class" in obj.attrs.keys():
      if obj.attrs["NX_class"] in ["NXentry", "NXsubentry"]:
        if "definition" in obj.keys():
          if obj["definition"].value == "NXmx":
            hits.append(obj)
  # run the visit on itself first
  visitor(entry, nx_file[entry])
  nx_file[entry].visititems(visitor)
  return hits

def validate(nx_file, item, test):
  '''
  Validate the NXmx entries

  '''
  values = []
  fails = []
  context = {}
  test(context, nx_file, item, values, fails)
  if len(fails) > 0:
    raise AssertionError('\n'.join(fails))
  return values

def check_path(nx_file, path):
  '''
  Ensure path exists

  '''
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
    entries = find_nx_mx_entries(self.file, self.entry)
    if len(entries) == 0:
      raise AssertionError('No NXmx entries found')
    return map(lambda entry: validate(
                self.file, 
                entry.name, 
                check_nx_mx()), entries)
