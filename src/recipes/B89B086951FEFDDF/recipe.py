import numpy as np


class Point:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.id = 0

    def set_id(self, index):
        self.id = index

    def point_string(self):
        return " ".join([str(self.x), str(self.y), str(self.z)]) + "\n"


class OFFFileCreator:

    _file_counter = 0

    def __init__(self, z, units):

        self.file_contents = "OFF\n"
        self.vertices = []
        self.vertex_counter = 0
        self.faces = []
        self.z = z

        self.file_name = (
            "chopper_geometry_" + str(OFFFileCreator._file_counter) + ".off"
        )
        OFFFileCreator._file_counter += 1

        if units == b"deg":
            self.cos = lambda x: np.cos(np.deg2rad(x))
            self.sin = lambda x: np.sin(np.deg2rad(x))
        else:
            self.cos = lambda x: np.cos(x)
            self.sin = lambda x: np.sin(x)

    def find_x(self, radius, theta):
        return radius * self.cos(theta)

    def find_y(self, radius, theta):
        return radius * self.sin(theta)

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

        outer_front_point, outer_back_point = self.create_mirrored_points(
            radius, slit_edge
        )
        inner_front_point, inner_back_point = self.create_mirrored_points(
            slit_height, slit_edge
        )

        self.add_vertex(outer_front_point)
        self.add_vertex(outer_back_point)
        self.add_vertex(inner_front_point)
        self.add_vertex(inner_back_point)

        self.add_face(
            [inner_front_point, outer_front_point, outer_back_point, inner_back_point]
        )

        return [
            outer_front_point,
            outer_back_point,
            inner_front_point,
            inner_back_point,
        ]

    def add_vertex(self, point):

        point.set_id(self.vertex_counter)
        self.vertices.append(point)
        self.vertex_counter += 1

    def add_vertices(self, points):

        for point in points:
            self.add_vertex(point)

    def add_face(self, points):

        ids = [point.id for point in points]
        self.faces.append(ids)

    def add_number_string_to_file(self, numbers):

        self.file_contents += " ".join([str(num) for num in numbers]) + "\n"

    def add_vertex_to_file(self, vertex):

        self.file_contents += vertex.point_string()

    def add_face_to_file(self, face):

        n_vertices = len(face)
        self.add_number_string_to_file([n_vertices] + face)

    def create_file_string(self):

        n_vertices = len(self.vertices)
        n_faces = len(self.faces)

        self.add_number_string_to_file([n_vertices, n_faces, 0])

        for vertex in self.vertices:
            self.add_vertex_to_file(vertex)

        for face in self.faces:
            self.add_face_to_file(face)

    def write_file(self):

        self.create_file_string()

        with open(self.file_name, "w") as f:
            f.write(self.file_contents)

        return self.file_name


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
        self.title = "Create an OFF file from an NXdisk_chopper"

        self.choppers = None
        self.resolution = 20

    def find_disk_choppers(self):
        """
        Find all of the disk_choppers contained in the file and return them in a list.
        """
        self.choppers = [self.file["entry"]["instrument"]["example_chopper"]]

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

    def generate_off_file(self, chopper, resolution, width):
        """
        Create an OFF file from a given chopper and user-defined width and resolution values.
        """

        radius, slit_height, slit_edges, units = self.get_chopper_data(chopper)

        off_creator = OFFFileCreator(width * 0.5, units)

        point_set = off_creator.create_and_add_point_set(
            radius, slit_height, slit_edges[0]
        )

        prev_outer_front = first_outer_front = point_set[0]
        prev_outer_back = first_outer_back = point_set[1]
        prev_inner_front = first_inner_front = point_set[2]
        prev_inner_back = first_inner_back = point_set[3]

        for i in range(1, len(slit_edges)):

            current_outer_front, current_outer_back, current_inner_front, current_inner_back = off_creator.create_and_add_point_set(
                radius, slit_height, slit_edges[i]
            )

            if i % 2:
                pass

            else:
                pass

            prev_outer_front = current_outer_front
            prev_outer_back = current_outer_back
            prev_inner_front = current_inner_front
            prev_inner_back = current_inner_back

        return off_creator.write_file()

    @staticmethod
    def ask_for_resolution():

        while True:

            res = input("Enter a resolution value: ")

            try:
                res = int(res)

                if res > 0:
                    return res
                else:
                    print(
                        "Resolution value "
                        + str(res)
                        + " is too small. Please try again."
                    )

            except ValueError:
                print("Could not convert " + res + " to an int. Please try again.")

    @staticmethod
    def ask_for_width():

        while True:

            width = input("Enter a width: ")

            try:
                width = float(width)

                if width > 0:
                    return width * 0.25
                else:
                    print(
                        "Width value " + str(width) + " is too small. Please try again."
                    )

            except ValueError:
                print("Could not convert " + width + " to a float. Please try again.")

    def process(self):
        """
        Recipes need to implement this method and return information which
        is useful to a user and instructive to a person reading the code.
        See some of the recommended examples for inspiration what to return.

        :return: the essence of the information recorded in this feature
        """

        self.find_disk_choppers()

        if not self.choppers:
            return "Unable to find disk choppers. No files created."

        else:

            resolution = self.ask_for_resolution()
            width = self.ask_for_width()

            output_file_names = []

            for chopper in self.choppers:

                output_file_names.append(
                    self.generate_off_file(chopper, resolution, width)
                )

            print("Successfully created file(s): " + ", ".join(output_file_names))
