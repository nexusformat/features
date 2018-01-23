import numpy as np


class GeometryExamples:
    """
    Example code to go from OFF file to NeXus file (see add_shape_from_off_file method)
    and from NeXus to OFF file (see output_shape_to_off_file).

    """
    def __init__(self, nx_entry):
        self.nx_entry = nx_entry

    def output_shape_to_off_file(self, off_filename):
        """
        Output the shape defined in an NXoff_geometry group to an OFF file

        :param filename: Name for the OFF file to output
        """
        geometry_groups = find_geometry_groups(self.nx_entry)
        # Build up vertices, faces and winding order
        vertices = None
        faces = None
        winding_order = None
        for group in geometry_groups:
            new_vertices, new_faces, new_winding_order = get_geometry_from_group(group, self.nx_entry)
            vertices, faces, winding_order, next_vertex = accumulate_geometry(vertices, faces, winding_order,
                                                                              new_vertices,
                                                                              new_faces, new_winding_order)
        write_off_file(off_filename, vertices, faces, winding_order)

    def add_shape_from_off_file(self, filename, group, name):
        """
        Add an NXoff_geometry shape definition from an OFF file

        :param filename: Name of the OFF file from which to get the geometry
        :param group: Group to add the NXoff_geometry to
        :param name: Name of the NXoff_geometry group to be created
        :return: NXoff_geometry group
        """
        with open(filename) as off_file:
            off_vertices, off_faces = self.parse_off_file(off_file)
        winding_order, faces = self.create_off_face_vertex_map(off_faces)
        shape = self.add_nx_group(group, name, 'NXoff_geometry')
        self.add_dataset(shape, 'vertices', np.array(off_vertices).astype('float32'), {'units': 'm'})
        self.add_dataset(shape, 'winding_order', np.array(winding_order).astype('int32'))
        self.add_dataset(shape, 'faces', np.array(faces).astype('int32'))
        return shape

    @staticmethod
    def skip_comment_lines(off_file):
        line = off_file.readline()
        while line[0] == '#':
            line = off_file.readline()
        return line

    @staticmethod
    def add_dataset(group, name, data, attributes=None):
        """
        Add a dataset to a given group

        :param group: Group object
        :param name: Name of the dataset to create
        :param data: Data to put in the dataset
        :param attributes: Optional dictionary of attributes to add to dataset
        :return: Dataset
        """
        if isinstance(data, str):
            dataset = group.create_dataset(name, data=np.array(data).astype('|S' + str(len(data))))
        else:
            dataset = group.create_dataset(name, data=data)

        if attributes:
            for key in attributes:
                if isinstance(attributes[key], str):
                    # Since python 3 we have to treat strings like this
                    dataset.attrs.create(key, np.array(attributes[key]).astype('|S' + str(len(attributes[key]))))
                else:
                    dataset.attrs.create(key, np.array(attributes[key]))
        return dataset

    @staticmethod
    def add_nx_group(parent_group, group_name, nx_class_name):
        """
        Add an NXclass group

        :param parent_group: The parent group object
        :param group_name: Name for the group, any spaces are replaced with underscores
        :param nx_class_name: Name of the NXclass
        :return: Group
        """
        group_name = group_name.replace(' ', '_')
        created_group = parent_group.create_group(group_name)
        created_group.attrs.create('NX_class', np.array(nx_class_name).astype('|S' + str(len(nx_class_name))))
        return created_group

    @staticmethod
    def create_off_face_vertex_map(off_faces):
        """
        Avoid having a ragged edge faces dataset due to differing numbers of vertices in faces by recording
        a flattened faces dataset (winding_order) and putting the start index for each face in that
        into the faces dataset.

        :param off_faces: OFF-style faces array, each row is number of vertices followed by vertex indices
        :return: flattened array (winding_order) and the start indices in that (faces)
        """
        faces = []
        winding_order = []
        current_index = 0
        for face in off_faces:
            faces.append(current_index)
            current_index += face[0]
            for vertex_index in face[1:]:
                winding_order.append(vertex_index)
        return winding_order, faces

    def parse_off_file(self, off_file):
        """
        Read vertex list and face definitions from an OFF file and return as lists of numpy arrays

        :param off_file: File object assumed to contain geometry description in OFF format
        :return: List of vertices and list of vertex indices in each face
        """
        file_start = off_file.readline()
        if file_start != 'OFF\n':
            raise RuntimeError('OFF file is expected to start "OFF", actually started: ' + file_start)
        line = self.skip_comment_lines(off_file)
        counts = line.split()
        number_of_vertices = int(counts[0])

        off_vertices = np.zeros((number_of_vertices, 3), dtype=float)  # preallocate
        vertex_number = 0
        while vertex_number < number_of_vertices:
            line = off_file.readline()
            if line[0] != '#':
                off_vertices[vertex_number, :] = np.array(line.split()).astype(float)
                vertex_number += 1

        faces_lines = off_file.readlines()

        all_faces = [np.array(face_line.split()).astype(int) for face_line in faces_lines if face_line[0] != '#']
        return off_vertices, all_faces


def contains_valid_geometry_groups(nx_file, entry):
    """
    Determine if file and NXentry contains valid geometry information

    :param nx_file: File to look in
    :param entry: NXentry to look in
    :return: True if file and NXentry contain geometry information
    """

    def _visit_group(name, obj):
        if "NX_class" in obj.attrs.keys():
            if str(obj.attrs["NX_class"], 'utf8') in ["NXoff_geometry", "NXcylindrical_geometry"]:
                validate(obj)
                return True  # causes visititems to terminate

    return nx_file[entry].visititems(_visit_group) is True


def validate(nx_geometry):
    """
    Checks NXoff_geometry or NXcylindrical_geometry group has expected datasets.

    :param nx_geometry: An NXoff_geometry or NXcylindrical group which was found in the file
    """
    fails = []
    if str(nx_geometry.attrs["NX_class"], 'utf8') == "NXoff_geometry":
        required_fields = ['vertices', 'winding_order', 'faces']
        class_type = "NXoff_geometry"
    else:
        required_fields = ['vertices', 'cylinders']
        class_type = "NXcylindrical_geometry"
    for field in required_fields:
        if field not in nx_geometry:
            fails.append(
                class_type + ' group named ' + nx_geometry.name + ' should have "' + field + '" dataset')

    if len(fails) > 0:
        raise AssertionError('\n'.join(fails))


class recipe:
    """
    Geometry (NXoff_geometry, NXcylindrical_geometry) - examples convert between NeXus and OFF files

    Proposed by: matthew.d.jones@stfc.ac.uk
    """

    def __init__(self, filedesc, entrypath):
        """
        Recipes are required to set a descriptive self.title

        :param filedesc: h5py file object of the NeXus/HDF5 file
        :param entrypath: path of the entry containing this feature
        """
        self.file = filedesc
        self.entry = entrypath
        self.title = "Geometry (NXoff_geometry, NXcylindrical_geometry) - examples convert between NeXus and OFF files"

    def process(self):
        """
        Recipes need to implement this method and return information which
        is useful to a user and instructive to a person reading the code.
        See some of the recommended examples for inspiration what to return.

        :return: the essence of the information recorded in this feature
        """
        if not contains_valid_geometry_groups(self.file, self.entry):
            raise AssertionError("No valid geometry entries found")
        else:
            return GeometryExamples(self.entry)
