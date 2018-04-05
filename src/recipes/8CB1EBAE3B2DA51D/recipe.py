import h5py
import numpy as np


class NeXusOFF:
    """
    Code to go from OFF file to NeXus file (see add_shape_from_off_file method)
    and from NeXus to OFF file (see output_shape_to_off_file).

    """

    def __init__(self, nx_entry):
        self.nx_entry = nx_entry
        self.vertices_per_cylinder = 10  # 10 corresponds to a pentagonal prism representation of a cylinder

    def output_shape_to_off_file(self, off_filename):
        """
        Output the complete geometry described in the given NXentry to a single OFF file

        NB.
        This function may have a long run time and high memory use for instruments with large geometry definitions,
        particularly for instruments with many cylindrical pixels. The number of vertices in the OFF description
        for cylinders (self.vertices_per_cylinder) has a strong impact on performance; it is recommended to start with
        a low value of 10 and increase if run time and memory-use permit.

        :param off_filename: Name for the OFF file to output
        """
        geometry_groups = self.find_geometry_groups()
        # Build up vertices, faces and winding order
        vertices = None
        faces = None
        winding_order = None
        for group in geometry_groups:
            new_vertices, new_faces, new_winding_order = self.get_geometry_from_group(group)
            vertices, faces, winding_order = self.accumulate_geometry(vertices, faces, winding_order, new_vertices,
                                                                      new_faces, new_winding_order)
        self.write_off_file(off_filename, vertices, faces, winding_order)

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

    def find_geometry_groups(self):
        """
        Find all kinds of group containing geometry information.
        Geometry groups themselves are often links (to reuse repeated geometry) so look for parents of geometry groups
        instead and return parent and child dictionary pairs.

        :return: list of geometry groups and their parent group
        """
        hits = []

        def _visit_groups(name, obj):
            if isinstance(obj, h5py.Group):
                for child_name in obj:
                    child = obj[child_name]
                    if isinstance(child, h5py.Group):
                        if "NX_class" in child.attrs.keys():
                            if str(child.attrs["NX_class"], 'utf8') in ["NXoff_geometry", "NXcylindrical_geometry"]:
                                hits.append({'parent_group': obj, 'geometry_group': child})

        self.nx_entry.visititems(_visit_groups)
        return hits

    @staticmethod
    def get_off_geometry_from_group(group):
        """
        Get geometry information from an NXoff_geometry group

        :param group:  NXoff_geometry and parent group in dictionary
        :return: vertices, faces and winding_order information from the group
        """
        vertices = group['geometry_group']['vertices'][...]
        return vertices, group['geometry_group']['faces'][...], group['geometry_group']['winding_order'][...]

    def get_cylindrical_geometry_from_group(self, group):
        """
        Get geometry information from an NXcylindrical_geometry group

        :param group:  NXcylindrical_geometry group and its parent group in a dictionary
        :return: vertices, faces and winding_order information from the group
        """
        cylinders = group['geometry_group']['cylinders'][...]
        group_vertices = group['geometry_group']['vertices'][...]
        vertices = None
        faces = None
        winding_order = None
        for cylinder in cylinders:
            vector_a = group_vertices[cylinder[0], :]
            vector_b = group_vertices[cylinder[1], :]
            vector_c = group_vertices[cylinder[2], :]

            axis = vector_a - vector_c
            unit_axis, height = self.normalise(axis)
            radius = self.calculate_magnitude(vector_b - vector_a)
            centre = (vector_a + vector_c) * 0.5

            mesh_vertices, mesh_faces = self.construct_cylinder_mesh(height, radius, unit_axis, centre,
                                                                     self.vertices_per_cylinder)
            new_winding_order, new_faces = self.create_off_face_vertex_map(mesh_faces)
            vertices, faces, winding_order = self.accumulate_geometry(vertices, faces, winding_order, mesh_vertices,
                                                                      new_faces, new_winding_order)
        return vertices, faces, winding_order

    def get_geometry_from_group(self, group):
        """
        Get geometry information from the geometry group

        :param group: Geometry group and its parent group in a dictionary
        :return: vertices, faces and winding_order information from the group
        """
        if str(group['geometry_group'].attrs["NX_class"], 'utf8') == "NXoff_geometry":
            vertices, faces, winding_order = self.get_off_geometry_from_group(group)
        elif str(group['geometry_group'].attrs["NX_class"], 'utf8') == "NXcylindrical_geometry":
            vertices, faces, winding_order = self.get_cylindrical_geometry_from_group(group)
        else:
            raise Exception('nexustooff.get_geometry_from_group was passed a group which is not a geometry type')
        vertices = np.matrix(vertices)
        vertices, faces, winding_order = self.replicate_if_pixel_geometry(group, vertices, faces, winding_order)
        vertices = self.get_and_apply_transformations(group, vertices)
        return vertices, faces, winding_order

    def replicate_if_pixel_geometry(self, group, vertices, faces, winding_order):
        """
        If the geometry group describes the shape of a single pixel then replicate the shape at all pixel offsets
        to find the shape of the whole detector panel.

        :param group: Geometry group and its parent group in a dictionary
        :param vertices: Vertices array for the original pixel
        :param faces: Faces array for the original pixel
        :param winding_order: Winding order array for the original pixel
        :return: vertices, faces, winding_order for the geometry comprising all pixels
        """
        if group['geometry_group'].name.split('/')[-1] == "pixel_shape":
            x_offsets, y_offsets, z_offsets = self.get_pixel_offsets(group)
            pixel_vertices = vertices
            pixel_faces = faces
            pixel_winding_order = winding_order
            next_indices = {'vertex': 0, 'face': 0, 'winding_order': 0}
            number_of_pixels = len(x_offsets)
            total_num_of_vertices = number_of_pixels * pixel_vertices.shape[0]

            # Preallocate arrays
            vertices = np.empty((total_num_of_vertices, 3))
            winding_order = np.empty((len(pixel_winding_order) * number_of_pixels), dtype=int)
            faces = np.empty((len(pixel_faces) * number_of_pixels), dtype=int)

            for pixel_number in range(number_of_pixels):
                new_vertices = np.hstack((pixel_vertices[:, 0] + x_offsets[pixel_number],
                                          pixel_vertices[:, 1] + y_offsets[pixel_number],
                                          pixel_vertices[:, 2] + z_offsets[pixel_number]))
                vertices, faces, winding_order, next_vertex = \
                    self.accumulate_geometry_in_prealloc_arrays(vertices, faces, winding_order, new_vertices,
                                                                pixel_faces, pixel_winding_order, next_indices)
        return vertices, faces, winding_order

    @staticmethod
    def accumulate_geometry(vertices, faces, winding_order, new_vertices, new_faces, new_winding_order):
        """
        Accumulate geometry from different groups in the NeXus file, or repeated pixels.

        :param vertices: Vertices array to accumulate in
        :param faces: Faces array to accumulate in
        :param winding_order: Winding order array to accumulate in
        :param new_vertices: (2D) New vertices to append/insert
        :param new_faces: (1D) New vertices to append
        :param new_winding_order: (1D) New winding_order to append
        """
        if faces is not None:
            faces = np.concatenate((faces, new_faces + winding_order.size))
        else:
            faces = np.array(new_faces)

        if winding_order is not None:
            winding_order = np.concatenate((winding_order, new_winding_order + vertices.shape[0]))
        else:
            winding_order = np.array(new_winding_order)

        if vertices is not None:
            vertices = np.vstack((vertices, new_vertices))
        else:
            vertices = new_vertices

        return vertices, faces, winding_order

    @staticmethod
    def accumulate_geometry_in_prealloc_arrays(vertices, faces, winding_order, new_vertices, new_faces,
                                               new_winding_order, next_indices):
        """
        Accumulate geometry from different groups in the NeXus file, or repeated pixels.
        Arrays are assumed to be preallocated and new data are inserted at the given index instead.

        :param vertices: Vertices array to accumulate in
        :param faces: Faces array to accumulate in
        :param winding_order: Winding order array to accumulate in
        :param new_vertices: (2D) New vertices to append/insert
        :param new_faces: (1D) New vertices to append
        :param new_winding_order: (1D) New winding_order to append
        :param next_indices: Insert new data at these indices
        """
        faces[next_indices['face']:(next_indices['face'] + len(new_faces))] = new_faces + next_indices[
            'winding_order']

        winding_order[next_indices['winding_order']:(next_indices['winding_order'] + len(new_winding_order))] = \
            new_winding_order + next_indices['vertex']

        vertices[next_indices['vertex']:(next_indices['vertex'] + new_vertices.shape[0]), :] = new_vertices

        next_indices['face'] += len(new_faces)
        next_indices['winding_order'] += len(new_winding_order)
        next_indices['vertex'] += new_vertices.shape[0]

        return vertices, faces, winding_order, next_indices

    @staticmethod
    def get_pixel_offsets(group):
        if 'x_pixel_offset' in group['parent_group']:
            x_offsets = group['parent_group']['x_pixel_offset'][...]
        else:
            raise Exception("No x_pixel_offset found in parent group of " + group['geometry_group'].name)
        if 'y_pixel_offset' in group['parent_group']:
            y_offsets = group['parent_group']['y_pixel_offset'][...]
        else:
            raise Exception("No y_pixel_offset found in parent group of " + group['geometry_group'].name)
        if 'z_pixel_offset' in group['parent_group']:
            z_offsets = group['parent_group']['z_pixel_offset'][...]
        else:
            z_offsets = np.zeros(x_offsets.shape)
        return x_offsets, y_offsets, z_offsets

    def get_and_apply_transformations(self, group, vertices):
        transformations = list()
        try:
            depends_on = group['parent_group'].get('depends_on')
        except:
            depends_on = '.'
        self.get_transformations(depends_on, transformations)

        vertices = np.matrix(vertices.T)
        # Add fourth element of 1 to each vertex, indicating these are positions not direction vectors
        vertices = np.matrix(np.vstack((vertices, np.ones(vertices.shape[1]))))
        vertices = self.do_transformations(transformations, vertices)
        # Now the transformations are done we do not need the 4th element
        return vertices[:3, :].T

    def get_transformations(self, depends_on, transformations):
        """
        Get all transformations in the depends_on chain
        NB, these need to then be applied in reverse order

        :param depends_on: The first depends_on path string
        :param transformations: List of transformations to populate
        """
        if depends_on is not None:
            try:
                transform_path = str(depends_on[...].astype(str))
            except:
                transform_path = depends_on.decode()
            if transform_path != '.':
                transform = self.nx_entry.get(transform_path)
                next_depends_on = self.get_transformation(transform, transformations)
                self.get_transformations(next_depends_on, transformations)

    def get_transformation(self, transform, transformations):
        attributes = transform.attrs
        offset = [0., 0., 0.]
        if 'offset' in attributes:
            offset = attributes['offset'].astype(float)
        if attributes['transformation_type'].astype(str) == 'translation':
            vector = attributes['vector'] * transform[...].astype(float)
            matrix = np.matrix([[1., 0., 0., vector[0] + offset[0]],
                                [0., 1., 0., vector[1] + offset[1]],
                                [0., 0., 1., vector[2] + offset[2]],
                                [0., 0., 0., 1.]])
            transformations.append(matrix)

        elif attributes['transformation_type'].astype(str) == 'rotation':
            axis = attributes['vector']
            angle = np.deg2rad(transform[...])
            rotation_matrix = self.rotation_matrix_from_axis_and_angle(axis, angle)
            matrix = np.matrix([[rotation_matrix[0, 0], rotation_matrix[0, 1], rotation_matrix[0, 2], offset[0]],
                                [rotation_matrix[1, 0], rotation_matrix[1, 1], rotation_matrix[1, 2], offset[1]],
                                [rotation_matrix[2, 0], rotation_matrix[2, 1], rotation_matrix[2, 2], offset[2]],
                                [0., 0., 0., 1.]])
            transformations.append(matrix)
        return attributes['depends_on']

    @staticmethod
    def do_transformations(transformations, vertices):
        for transformation in transformations:
            for column_index in range(vertices.shape[1]):
                vertices[:, column_index] = transformation * np.matrix(vertices[:, column_index])
        return vertices

    def write_off_file(self, filename, vertices, faces, winding_order):
        """
        Create an OFF format file

        :param filename: Name for the OFF file to output
        :param vertices: 2D array contains x, y, z coords for each vertex
        :param faces: 1D array indexing into winding_order at the start of each face
        :param winding_order: 1D array of vertex indices in the winding order for each face
        """
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
                self.write_off_face(verts_in_face, off_file)
                previous_index = face
            # Last face is the last face index to the end of the winding_order list
            verts_in_face = winding_order[previous_index:]
            self.write_off_face(verts_in_face, off_file)

    @staticmethod
    def write_off_face(verts_in_face, off_file):
        """
        Write line in the OFF file corresponding to a single face in the geometry

        :param verts_in_face: Indices in the vertex list of the vertices in this face
        :param off_file:  Handle of the file to write to
        """
        fmt_str = '{} ' * (len(verts_in_face) + 1)
        fmt_str = fmt_str[:-1] + '\n'
        off_file.write(fmt_str.format(len(verts_in_face), *verts_in_face).encode('utf8'))

    def construct_cylinder_mesh(self, height, radius, axis, centre=None, number_of_vertices=50):
        """
        Construct an NXoff_geometry description of a cylinder

        :param height: Height of the tube
        :param radius: Radius of the tube
        :param axis: Axis of the tube as a unit vector
        :param centre: On-axis centre of the tube in form [x, y, z]
        :param number_of_vertices: Maximum number of vertices to use to describe pixel
        :return: vertices and faces (corresponding to OFF description)
        """
        # Construct the geometry as if the tube axis is along x, rotate everything later
        if centre is None:
            centre = [0, 0, 0]
        face_centre = [centre[0] - (height / 2.0), centre[1], centre[2]]
        angles = np.linspace(0, 2 * np.pi, np.floor((number_of_vertices / 2) + 1))
        # The last point is the same as the first so get rid of it
        angles = angles[:-1]
        y = face_centre[1] + radius * np.cos(angles)
        z = face_centre[2] + radius * np.sin(angles)
        num_points_at_each_tube_end = len(y)
        vertices = np.concatenate((
            np.array(list(zip(np.zeros(len(y)) + face_centre[0], y, z))),
            np.array(list(zip(np.ones(len(y)) * height + face_centre[0], y, z)))))

        # Rotate vertices to correct the tube axis
        try:
            rotation_matrix = self.find_rotation_matrix_between_vectors(np.array(axis), np.array([1., 0., 0.]))
        except:
            rotation_matrix = None
        if rotation_matrix is not None:
            vertices = rotation_matrix.dot(vertices.T).T

        #
        # points around left circle tube-end       points around right circle tube-end
        #                                          (these follow the left ones in vertices list)
        #  circular boundary ^                     ^
        #                    |                     |
        #     nth_vertex + 2 .                     . nth_vertex + num_points_at_each_tube_end + 2
        #     nth_vertex + 1 .                     . nth_vertex + num_points_at_each_tube_end + 1
        #     nth_vertex     .                     . nth_vertex + num_points_at_each_tube_end
        #                    |                     |
        #  circular boundary v                     v
        #
        # face starts with the number of vertices in the face (4)
        faces = [
            [4, nth_vertex, nth_vertex + num_points_at_each_tube_end, nth_vertex + num_points_at_each_tube_end + 1,
             nth_vertex + 1] for nth_vertex in range(num_points_at_each_tube_end - 1)]
        # Append the last rectangular face
        faces.append([4, num_points_at_each_tube_end - 1, (2 * num_points_at_each_tube_end) - 1,
                      num_points_at_each_tube_end, 0])
        # NB this is a tube, not a cylinder; I'm not adding the circular faces on the ends of the tube
        faces = np.array(faces)
        return vertices, faces

    @staticmethod
    def calculate_magnitude(input_vector):
        return np.sqrt(np.sum(np.square(input_vector.astype(float))))

    def normalise(self, input_vector):
        """
        Normalise to unit vector

        :param input_vector: Input vector (numpy array)
        :return: Unit vector, magnitude
        """
        magnitude = self.calculate_magnitude(input_vector)
        if magnitude == 0:
            return np.array([0.0, 0.0, 0.0]), 0.0
        unit_vector = input_vector.astype(float) / magnitude
        return unit_vector, magnitude

    @staticmethod
    def rotation_matrix_from_axis_and_angle(axis, theta):
        """
        Calculate the rotation matrix for rotating angle theta about axis

        :param axis: 3D unit vector axis
        :param theta: Angle to rotate about axis in radians
        :return: 3x3 rotation matrix
        """
        axis_x = axis[0]
        axis_y = axis[1]
        axis_z = axis[2]
        cos_t = np.cos(theta)
        sin_t = np.sin(theta)
        rotation_matrix_row_1 = np.array([cos_t + axis_x ** 2.0 * (1 - cos_t),
                                          axis_x * axis_y * (1 - cos_t) - axis_z * sin_t,
                                          axis_x * axis_z * (1 - cos_t) + axis_y * sin_t])
        rotation_matrix_row_2 = np.array([axis_y * axis_x * (1 - cos_t) + axis_z * sin_t,
                                          cos_t + axis_y ** 2.0 * (1 - cos_t),
                                          axis_y * axis_z * (1 - cos_t) - axis_x * sin_t])
        rotation_matrix_row_3 = np.array([axis_z * axis_x * (1 - cos_t) - axis_y * sin_t,
                                          axis_z * axis_y * (1 - cos_t) + axis_x * sin_t,
                                          cos_t + axis_z ** 2.0 * (1 - cos_t)])
        rotation_matrix = np.array([rotation_matrix_row_1, rotation_matrix_row_2, rotation_matrix_row_3])
        return rotation_matrix

    def find_rotation_matrix_between_vectors(self, vector_a, vector_b):
        """
        Find the 3D rotation matrix to rotate vector_a onto vector_b

        :param vector_a: 3D vector
        :param vector_b: 3D vector
        :return: 3D rotation matrix
        """
        unit_a, mag_a = self.normalise(vector_a)
        unit_b, mag_b = self.normalise(vector_b)
        identity_matrix = np.identity(3)

        if np.allclose(unit_a, unit_b):
            return identity_matrix

        axis, angle = self.find_rotation_axis_and_angle_between_vectors(vector_a, vector_b)

        skew_symmetric = np.array([np.array([0.0, -axis[2], axis[1]]),
                                   np.array([axis[2], 0.0, -axis[0]]),
                                   np.array([-axis[1], axis[0], 0.0])])

        rotation_matrix = identity_matrix + np.sin(angle) * skew_symmetric + \
                          ((1.0 - np.cos(angle)) * (skew_symmetric ** 2.0))
        return rotation_matrix

    def find_rotation_axis_and_angle_between_vectors(self, vector_a, vector_b):
        """
        Find the axis and angle of rotation to rotate vector_a onto vector_b

        :param vector_a: 3D vector
        :param vector_b: 3D vector
        :return: axis, angle
        """
        unit_a, mag_a = self.normalise(vector_a)
        unit_b, mag_b = self.normalise(vector_b)

        if np.allclose(unit_a, unit_b):
            print('Vectors coincide; no rotation required in nexusutils.find_rotation_axis_and_angle_between_vectors')
            return None, None

        cross_prod = np.cross(vector_a, vector_b)
        unit_cross, mag_cross = self.normalise(cross_prod)

        def is_close(a, b, rel_tol=1e-09, abs_tol=0.0):
            return abs(a - b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)

        if is_close(mag_cross, 0.0):
            raise NotImplementedError('No unique solution for rotation axis in '
                                      'find_rotation_axis_and_angle_between_vectors()')

        axis = cross_prod / mag_cross
        angle = -1.0 * np.arccos(np.dot(vector_a, vector_b) / (mag_a * mag_b))

        return axis, angle


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
    Geometrical Shape (NXoff_geometry, NXcylindrical_geometry) - extract OFF data (files) from NeXus

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
        self.title = "Geometrical Shape (NXoff_geometry, NXcylindrical_geometry) - extract OFF data (files) from NeXus"

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
            return NeXusOFF(self.entry)


# This allows recipe.py to be run directly as a test/demonstration
if __name__ == "__main__":
    nx_file = h5py.File("../../../examples/example_nx_geometry.nxs", "r")
    example = NeXusOFF(nx_file["raw_data_1"])
    example.output_shape_to_off_file("example.off")
    # example.off can be opened by CAD or 3D rendering software such as Geomview (http://www.geomview.org/)
