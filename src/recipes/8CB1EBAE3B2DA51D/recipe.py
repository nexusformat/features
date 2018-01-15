import numpy as np


class NXoff_geometryExamples:
    """
    Example code to go from OFF file to NeXus file (see add_shape_from_off_file method)
    and from NeXus to OFF file (see output_shape_to_off_file).

    """

    def __init__(self, nx_off_group):
        self.nx_off_group = nx_off_group

    def output_shape_to_off_file(self, filename):
        """
        Output the shape defined in an NXoff_geometry group to an OFF file

        :param filename: Name for the OFF file to output
        """
        vertices = self.nx_off_group['vertices'][...]
        faces = self.nx_off_group['faces'][...]
        winding_order = self.nx_off_group['winding_order'][...]
        number_of_vertices = len(vertices)
        number_of_faces = len(faces) - 1
        # According to OFF standard the number of edges must be present but does not need to be correct
        number_of_edges = 0
        with open(filename, 'wb') as off_file:
            off_file.write('OFF\n'.encode('utf8'))
            off_file.write('# NVertices NFaces NEdges\n'.encode('utf8'))
            off_file.write('{} {} {}\n'.format(number_of_vertices, number_of_faces, number_of_edges).encode('utf8'))

            off_file.write('# Vertices\n'.encode('utf8'))
            np.savetxt(off_file, vertices, fmt='%f', delimiter=" ")

            off_file.write('# Faces\n'.encode('utf8'))
            previous_index = 0
            for face in faces[1:]:
                verts_in_face = winding_order[previous_index:face]
                number_of_verts_in_face = len(verts_in_face)
                fmt_str = '{} ' * (number_of_verts_in_face + 1)
                fmt_str = fmt_str[:-1] + '\n'
                off_file.write(fmt_str.format(number_of_verts_in_face, *verts_in_face).encode('utf8'))
                previous_index = face

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


class _NXoff_geometryFinder:
    """
    Finds NXoff_geometry groups in the file
    """

    def __init__(self):
        self.hits = []

    def _visit_NXoff_geometry(self, name, obj):
        if "NX_class" in obj.attrs.keys():
            if "NXoff_geometry" == str(obj.attrs["NX_class"], 'utf8'):
                self.hits.append(obj)

    def get_NXoff_geometry(self, nx_file, entry):
        self.hits = []
        nx_file[entry].visititems(self._visit_NXoff_geometry)
        return self.hits


def validate(nx_off_geometry):
    """
    Checks that lengths of datasets which should be the same length as each other are.

    :param nx_off_geometry: An NXoff_geometry group which was found in the file
    """
    fails = []
    required_fields = ['vertices', 'winding_order', 'faces']
    for field in required_fields:
        if field not in nx_off_geometry:
            fails.append(
                'NXoff_geometry group named ' + nx_off_geometry.name + ' should have "' + field + '" dataset')

    if len(fails) > 0:
        raise AssertionError('\n'.join(fails))


class recipe:
    """
    NXoff_geometry - examples converting between NeXus and OFF files

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
        self.title = "NXoff_geometry - examples converting between NeXus and OFF files"

    def process(self):
        """
        Recipes need to implement this method and return information which
        is useful to a user and instructive to a person reading the code.
        See some of the recommended examples for inspiration what to return.

        :return: the essence of the information recorded in this feature
        """
        nx_off_finder = _NXoff_geometryFinder()
        nx_off_list = nx_off_finder.get_NXoff_geometry(self.file, self.entry)
        if len(nx_off_list) == 0:
            raise AssertionError("No NXoff_geometry entries found")
        examples = []
        for nx_off_entry in nx_off_list:
            validate(nx_off_entry)
            examples.append(NXoff_geometryExamples(nx_off_entry))

        return examples
