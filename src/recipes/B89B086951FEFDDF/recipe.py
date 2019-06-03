import numpy as np


class Point:
    """
    Basic class for representing a point with an index.
    """

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.id = None

    def set_id(self, index):
        """
        Give the point an ID. Attempts to make sure this can only be done once.
        """
        if self.id is None and index is not None:
            self.id = index

    def point_string(self):
        """
        Create a string from the point coordinates to that it can be placed in the OFF file.
        """

        return " ".join([str(self.x), str(self.y), str(self.z)]) + "\n"


class OFFFileCreator:
    """
    Tool for creating OFF files from NXdisk_chopper information.
    """

    _file_counter = 0

    def __init__(self, z):

        self.file_contents = "OFF\n"
        self.vertices = []
        self.faces = []
        self.z = z

        self.file_name = (
            "chopper_geometry_" + str(OFFFileCreator._file_counter) + ".off"
        )
        OFFFileCreator._file_counter += 1

        self.front_centre = Point(0, 0, self.z)
        self.add_vertex_to_list(self.front_centre)
        self.back_centre = Point(0, 0, -self.z)
        self.add_vertex_to_list(self.back_centre)

    @staticmethod
    def find_x(radius, theta):
        return radius * np.cos(theta)

    @staticmethod
    def find_y(radius, theta):
        return radius * np.sin(theta)

    def create_mirrored_points(self, r, theta):
        """
        Creates two points that share the same x and y values and have a different z value.
        :param r: The distance between the points and their respective 'origins' ([0,0,+z] and [0,0,-z]).
        :param theta: The angle of the points.
        :return: Two points that have a distance of 2*z from each other.
        """

        x = self.find_x(r, theta)
        y = self.find_y(r, theta)

        return Point(x, y, self.z), Point(x, y, -self.z)

    def create_and_add_point_set(self, radius, slit_height, slit_edge):
        """
        Creates the upper and lower points for a slit edge and adds these to the OFF file. Also adds the face made from
        all four points to the OFF file.
        :param radius: The radius of the disk chopper.
        :param slit_height: The height of the slit.
        :param slit_edge: The angle of the slit in radians.
        :return: The Point objects for the four vertices with the same angle.
        """

        upper_front_point, upper_back_point = self.create_mirrored_points(
            radius, slit_edge
        )
        lower_front_point, lower_back_point = self.create_mirrored_points(
            slit_height, slit_edge
        )

        self.add_vertex_to_list(upper_front_point)
        self.add_vertex_to_list(upper_back_point)
        self.add_vertex_to_list(lower_front_point)
        self.add_vertex_to_list(lower_back_point)

        self.add_face_to_list(
            [lower_front_point, upper_front_point, upper_back_point, lower_back_point]
        )

        return [
            upper_front_point,
            upper_back_point,
            lower_front_point,
            lower_back_point,
        ]

    def create_and_add_mirrored_points(self, r, theta):
        """
        Creates two mirrored points and adds these to the list of vertices.
        :param r: The distance between the point and front/back centre of the disk chopper.
        :param theta: The angle of the point
        :return: The Point objects for the mirrored points.
        """

        front, back = self.create_mirrored_points(r, theta)
        self.add_vertex_to_list(front)
        self.add_vertex_to_list(back)

        return front, back

    def add_face_connected_to_front_centre_to_list(self, points):
        """
        Creates a face that is connected to the center point on the front of the disk chopper.
        :param points: The points that make up the face minus the centre point.
        """
        self.add_face_to_list([self.front_centre] + points)

    def add_face_connected_to_back_centre_to_list(self, points):
        """
        Creates a face that is connected to the center point on the back of the disk chopper.
        :param points: The points that make up the face minus the centre point.
        """
        self.add_face_to_list([self.back_centre] + points)

    def add_vertex_to_list(self, point):
        """
        Adds a point to the list of vertices and gives it an ID.
        :param point: The point that is added to the list of vertices.
        """
        point.set_id(len(self.vertices))
        self.vertices.append(point)

    def add_face_to_list(self, points):
        """
        Adds a face to the list of faces by creating a list of its vertex IDs.
        :param points: A list of the points that compose the face.
        """
        ids = [point.id for point in points]
        self.faces.append(ids)

    def add_number_string_to_file_string(self, numbers):
        """
        Adds a list of numbers separated by a space to the OFF file string.
        :param numbers: The list of numbers that will go in the OFF file.
        """
        self.file_contents += " ".join([str(num) for num in numbers]) + "\n"

    def add_vertex_to_file_string(self, vertex):
        """
        Adds a vertex to the OFF file contents string by obtaining its point string.
        :param vertex: The vertex that is added to the file string.
        """
        self.file_contents += vertex.point_string()

    def add_face_to_file_string(self, face):
        """
        Adds a face to the OFF file string using a list of the vertex IDs.
        :param face: A list of the IDs of the vertices that make the face.
        """

        n_vertices = len(face)
        self.add_number_string_to_file_string([n_vertices] + face)

    def create_file_string(self):
        """
        Create the string that stores all the information needed in the OFF file.
        """

        n_vertices = len(self.vertices)
        n_faces = len(self.faces)

        # Add vertex count and face count to the file. Leave out number of edges as this is optional.
        self.add_number_string_to_file_string([n_vertices, n_faces, 0])

        # Add the vertex coordinates to the string
        for vertex in self.vertices:
            self.add_vertex_to_file_string(vertex)

        # Add the face information to the string
        for face in self.faces:
            self.add_face_to_file_string(face)

    def write_off_file(self):
        """
        Create a string of OFF file data and write this to a file.
        :return The filename of the generated OFF file.
        """
        self.create_file_string()

        with open(self.file_name, "w") as f:
            f.write(self.file_contents)

        return self.file_name


class _NXDiskChopperFinder(object):
    def __init__(self):
        self.hits = []

    def _visit_NXdisk_chopper(self, name, obj):
        if "NX_class" in obj.attrs.keys():
            if str(obj.attrs["NX_class"], "utf8") == "NXdisk_chopper":
                self.hits.append(obj)

    def get_NXdisk_chopper(self, nx_file, entry):
        self.hits = []
        nx_file[entry].visititems(self._visit_NXdisk_chopper)
        return self.hits


class recipe:
    """
    Generate OFF files from the NXdisk_choppers that are present in the NeXus file.

    Proposed by: dolica.akello-egwel@stfc.ac.uk
    """

    def __init__(self, filedesc, entrypath):
        """
        Recipes are required to set a descriptive self.title

        :param filedesc: h5py file object of the NeXus/HDF5 file
        :param entrypath: path of the entry containing this feature
        """

        self.file = filedesc
        self.entry = entrypath
        self.title = "Create an OFF file from an NXdisk_chopper. Mesh resolution and width can be changed from the recipe __init__ method."

        self.choppers = None

        # Number of "slices" in the chopper excluding slit boundaries. Must be zero or greater. A higher value makes the mesh more detailed.
        self.resolution = 30
        self.resolution_angles = None

        # The width of the disk chopper
        self.width = 50

    @staticmethod
    def get_chopper_data(chopper):
        """
        Extract radius, slit_height, slit_edges, and angle units data from a given chopper group.
        """
        radius = chopper["radius"][()]
        slit_height = chopper["slit_height"][()]
        slit_edges = chopper["slit_edges"][()]
        units = chopper["slit_edges"].attrs["units"]

        return radius, slit_height, slit_edges, units

    def create_intermediate_points_and_faces(
        self,
        off_creator,
        first_angle,
        second_angle,
        first_front,
        first_back,
        second_front,
        second_back,
        r,
    ):

        if second_angle > first_angle:
            intermediate_angles = self.resolution_angles[
                (self.resolution_angles > first_angle)
                & (self.resolution_angles < second_angle)
            ]
        else:
            # Use append rather than an or operator because the larger values need to appear first
            intermediate_angles = np.append(
                self.resolution_angles[(self.resolution_angles > first_angle)],
                self.resolution_angles[(self.resolution_angles < second_angle)],
            )

        prev_front = first_front
        prev_back = first_back

        for angle in intermediate_angles:

            current_front, current_back = off_creator.create_and_add_mirrored_points(
                r, angle
            )
            off_creator.add_face_to_list(
                [prev_front, prev_back, current_back, current_front]
            )
            off_creator.add_face_connected_to_front_centre_to_list(
                [prev_front, current_front]
            )
            off_creator.add_face_connected_to_back_centre_to_list(
                [prev_back, current_back]
            )
            prev_front = current_front
            prev_back = current_back

        off_creator.add_face_to_list([prev_front, prev_back, second_back, second_front])
        off_creator.add_face_connected_to_front_centre_to_list(
            [prev_front, second_front]
        )
        off_creator.add_face_connected_to_back_centre_to_list([prev_back, second_back])

    def generate_off_file(self, chopper, resolution, width):
        """
        Create an OFF file from a given chopper and user-defined width and resolution values.
        """

        # Obtain the radius, slit height, slit angles, and units from the chopper data
        radius, slit_height, slit_edges, units = self.get_chopper_data(chopper)

        # Convert the slit edges to radians if they're in degrees
        if units == b"deg":
            slit_edges = [np.deg2rad(x) for x in slit_edges]

        off_creator = OFFFileCreator(width * 0.5)

        # Create four points for the first slit in the chopper data
        point_set = off_creator.create_and_add_point_set(
            radius, slit_height, slit_edges[0]
        )

        prev_upper_front = first_upper_front = point_set[0]
        prev_upper_back = first_upper_back = point_set[1]
        prev_lower_front = point_set[2]
        prev_lower_back = point_set[3]

        # Remove the first angle to avoid creating duplicate points at angle 0 and at angle 360
        self.resolution_angles = np.linspace(0, 2 * np.pi, resolution + 1)[1:]

        for i in range(1, len(slit_edges)):

            current_upper_front, current_upper_back, current_lower_front, current_lower_back = off_creator.create_and_add_point_set(
                radius, slit_height, slit_edges[i]
            )

            if i % 2:
                self.create_intermediate_points_and_faces(
                    off_creator,
                    slit_edges[i - 1],
                    slit_edges[i],
                    prev_lower_front,
                    prev_lower_back,
                    current_lower_front,
                    current_lower_back,
                    slit_height,
                )
            else:
                self.create_intermediate_points_and_faces(
                    off_creator,
                    slit_edges[i - 1],
                    slit_edges[i],
                    prev_upper_front,
                    prev_upper_back,
                    current_upper_front,
                    current_upper_back,
                    radius,
                )

            prev_upper_front = current_upper_front
            prev_upper_back = current_upper_back
            prev_lower_front = current_lower_front
            prev_lower_back = current_lower_back

        self.create_intermediate_points_and_faces(
            off_creator,
            slit_edges[-1],
            slit_edges[0],
            prev_upper_front,
            prev_upper_back,
            first_upper_front,
            first_upper_back,
            radius,
        )

        return off_creator.write_off_file()

    def process(self):
        """
        Recipes need to implement this method and return information which
        is useful to a user and instructive to a person reading the code.
        See some of the recommended examples for inspiration what to return.

        :return: A list of the the filenames of the OFF files that have been created.
        """

        chopper_finder = _NXDiskChopperFinder()
        self.choppers = chopper_finder.get_NXdisk_chopper(self.file, self.entry)

        if not self.choppers:
            return "Unable to find disk choppers. No files created."

        else:

            output_file_names = []

            for chopper in self.choppers:

                output_file_names.append(
                    self.generate_off_file(chopper, self.resolution, self.width)
                )

            print("Successfully created file(s): " + ", ".join(output_file_names))
