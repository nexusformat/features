def check_len(context, entry, item, values, fails):
  frames = entry[item].shape[0];
  if (not 'nFrames' in context.keys()) and frames != 1:
    context['nFrames'] = frames
    context['nFrames_item'] = item
  else :
    if not frames in [context['nFrames'], 1]:
      fails.append("'%s' does not have the same number of frames as '%s'" % (item, context['nFrames_item']))

class check_dset(object):

  def __init__(self, dtype=None, dims=None, shape=None, same_shape_as=None):
    self.dtype = dtype
    self.dims = dims
    self.shape = shape
    self.same_shape_as = same_shape_as

  def __call__(self, context, entry, item, values, fails):
    from os.path import isabs, dirname, join
    if self.dtype is not None:
      dtype = entry[item].dtype
      if not dtype == self.dtype:
        fails.append("'%s' is of type %s, expected %s" % (
          item, dtype, self.dtype))
    if self.dims is not None:
      dims = len(entry[item].shape)
      if not dims == self.dims:
        fails.append("'%s' has dims=%d, expected %d" % (
          item, dims, self.dims))
    if self.shape is not None:
      shape = entry[item].shape
      if not shape == self.shape:
        fails.append("'%s' has shape=%s, expected %s" % (
          item, str(shape), str(self.shape)))
    if self.same_shape_as is not None:
      if not isabs(self.same_shape_as):
        other = join(dirname(item), self.same_shape_as)
      else:
        other = self.same_shape_as
      shape1 = entry[item].shape
      shape2 = entry[other].shape
      if not shape1 == shape2:
        fails.append("'%s' does not have same shape as '%s' (%s)" % (
          item, str(shape1), other, str(shape2)))

class check_depends_on(object):

  def __init__(self):
    pass

  def __call__(self, context, entry, item, values, fails):
    dependency_chain = []
    assert(item.count("@") <= 1)
    if item.count("@") == 1:
      item, attr = item.split("@")
      depends_on = entry[item].attrs[attr]
    else:
      depends_on = entry[item].value
    nx_file = entry.file
    while not depends_on == ".":
      if depends_on in dependency_chain:
        fails.append("'%s' is a circular dependency" % depends_on)
      try:
        item = nx_file[depends_on]
      except Exception:
        fails.append("'%s' is missing from nx_file" % depends_on)
        break
      dependency_chain.append(depends_on)
      try:
        depends_on = nx_file[depends_on].attrs["depends_on"]
      except Exception:
        fails.append("'%s' contains no depends_on attribute" % depends_on)
        break

class check_attr(object):

  def __init__(self, name, tests=None):
    self.name = name
    self.tests = tests

  def __call__(self, context, entry, item, values, fails):
    if not self.name in entry[item]:
      fails.append("'%s' does not have an attribute '%s'" % (
        item, self.name))
    if self.tests is not None:
      from os.path import join
      path = item
      for test in tests:
        test(context, entry, item + "@" + self.name, values, fails)

class check_nx_class(object):

  def __call__(self, context, entry, item, values, fails):
    from os.path import join
    path = item
    for item, detail in self.items.iteritems():
      item = join(path, item)
      min_occurs = detail['minOccurs']
      tests = detail['tests']
      assert(min_occurs in [0, 1])
      if check_path(entry, item):
        for test in tests:
          test(context, entry, item, values, fails)
      elif min_occurs == 1:
        fails.append("'%s' is missing from the NXmx entry" % (item))
    return values

class check_nx_detector_module(check_nx_class):

  def __init__(self):
    from os.path import join
      
    # The items to validate
    self.items = { 
      "data_origin" : { 
        "minOccurs" : 1, 
        "tests" : [
          check_dset(dtype="uint64", shape=(2,))
        ] 
      },
      "data_size" : { 
        "minOccurs" : 1, 
        "tests" : [
          check_dset(dtype="uint64", shape=(2,))
        ] 
      },
      "module_offset" : { 
        "minOccurs" : 1, 
        "tests" : [
          check_dset(dtype="uint64", shape=(1,)), 
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
          check_dset(dtype="float64", shape=(1,)), 
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
          check_dset(dtype="float64", shape=(1,)), 
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
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "dead_time" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "count_time" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "beam_centre_x" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "beam_centre_y" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "angular_calibration_applied" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="bool", shape=(1,))
        ]
      },
      "flatfield_applied" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="bool", shape=(1,))
        ]
      },
      "flatfield" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", same_shape_as="data")
        ]
      },
      "flatfield_error" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", same_shape_as="data")
        ]
      },
      "pixel_mask_applied" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="bool", shape=(1,))
        ]
      },
      "pixel_mask" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="int32", same_shape_as="data")
        ]
      },
      "countrate_correction_applied" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="bool", shape=(1,))
        ]
      },
      "bit_depth_readout" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="uint64", shape=(1,))
        ]
      },
      "detector_readout_time" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "frame_time" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "gain_setting" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "saturation_value" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="int64", shape=(1,))
        ]
      },
      "sensor_material" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "sensor_thickness" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "threshold_energy" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "type" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "transformations" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "detector_module" : {
        "minOccurs" : 1,
        "tests" : [
          check_nx_detector_module(),
        ]
      }
    } 

class check_nx_attenuator(check_nx_class):
  
  def __init__(self):
    self.items = {
      "attenuator_transmission" : {
        "minOccurs" : 1,
        "tests" : []
      }
    }

class check_nx_beam(check_nx_class):

  def __init__(self):
    self.items = {
      "distance" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "incident_energy" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64")
        ]
      },
      "final_energy" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64")
        ]
      },
      "energy_transfer" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64")
        ]
      },
      "incident_wavelength" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
      "incident_wavelength_spread" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64")
        ]
      },
      "incident_wavelength_spectrum" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "incident_beam_divergence" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64")
        ]
      },
      "final_wavelength" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64")
        ]
      },
      "incident_polarization" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64")
        ]
      },
      "incident_polarization_stokes" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "final_polarization" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64")
        ]
      },
      "final_wavelength_spread" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64")
        ]
      },
      "final_beam_divergence" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64")
        ]
      },
      "flux" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", shape=(1,))
        ]
      },
    }

class check_nx_sample(check_nx_class):

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
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", dims=2)
        ]
      },
      "unit_cell_class" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "unit_cell_group" : {
        "minOccurs" : 0,
        "tests" : []
      },
      "sample_orientation" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", shape=(3,))
        ]
      },
      "orientation_matrix" : {
        "minOccurs" : 0,
        "tests" : [
          check_dset(dtype="float64", dims=3)
        ]
      },
      "temperature" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "transformations" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "beam" : {
        "minOccurs" : 1,
        "tests" : [
          check_nx_beam()
        ]
      }
    }

class check_nx_mx(check_nx_class):
  
  def __init__(self):

    self.items = {
      'title' : {
        "minOccurs" : 1,
        "tests" : []
      },
      "start_time" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "end_time" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "data" : {
        "minOccurs" : 1,
        "tests" : [
          check_dset(dims=3)
        ]
      },
      "instrument" : {
        "minOccurs" : 1,
        "tests" : []
      },
      "instrument" : {
        "minOccurs" : 1,
        "tests" : [
          check_nx_attenuator()
        ]
      },
      "instrument/detector" : {
        "minOccurs" : 1,
        "tests" : [
          check_nx_detector()
        ],
      },
      "sample" : {
        "minOccurs" : 1,
        "tests" : [
          check_nx_sample(),
        ]
      }
    }

def find_nx_mx_entries(nx_file, entry):
  hits = []
  def visitor(name, obj):
    if "NX_class" in obj.attrs.keys():
      if obj.attrs["NX_class"] in ["NXentry", "NXsubentry"]:
        if "definition" in obj.keys():
          if obj["definition"].value == "NXmx":
            hits.append(obj)
  nx_file[entry].visititems(visitor)
  return hits

def validate(entry, test):
  values = []
  fails = []
  context = {}
  test(context, entry, '', values, fails)
  if len(fails) > 0:
    raise AssertionError('\n'.join(fails))
  return values

def check_path(entry, path):
  section = entry
  for part in path.split('/'):
    if part in section.keys():
      section = section[part]
    else :
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
    return map(lambda entry: validate(entry, check_nx_mx()), entries)
