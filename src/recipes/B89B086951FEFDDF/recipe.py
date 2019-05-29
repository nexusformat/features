import numpy as np


class Point:

    _counter = 0

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

        self.id = Point._counter
        Point._counter += 1

    def point_string(self):
        return " ".join([str(self.x), str(self.y), str(self.z)]) + "\n"


class OFFFileCreator:
    def __init__(self):

        self.file = "OFF\n"
        self.vertices = []
        self.faces = []
        self.front_vertices = []
        self.back_vertices = []

    def add_vertex(self, point):

        self.vertices.append(point)

    def add_face(self, points):

        ids = [point.id for point in points]
        self.faces.append(ids)

    def add_front_vertex(self, point):

        self.front_vertices.append(point)

    def add_back_vertex(self, point):

        self.back_vertices.append(point)

    def add_number_string(self, numbers):

        self.file += " ".join([str(num) for num in numbers]) + "\n"

    def add_vertex_to_file(self, vertex):

        self.file += vertex.point_string()

    def add_face_to_file(self, face):

        n_vertices = len(face)
        self.add_number_string([n_vertices] + face)

    def add_front_or_back_face_to_file(self, vertices):

        ids = [vertex.id for vertex in vertices]
        self.add_face_to_file(ids)

    def create_file(self):

        n_vertices = len(self.vertices)
        n_faces = len(self.faces)

        self.add_number_string([n_vertices, n_faces, 0])

        for vertex in self.vertices:
            self.add_vertex_to_file(vertex)

        for face in self.faces:
            self.add_face_to_file(face)

        # self.add_front_or_back_face_to_file(self.front_vertices)
        # self.add_front_or_back_face_to_file(self.back_vertices)

        return self.file


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
        self.z = 50

    def find_disk_choppers(self):
        """
        Find all of the disk_choppers contained in the file and return them in a list.
        """
        self.choppers = [self.file["entry"]["instrument"]["example_chopper"]]

    @staticmethod
    def get_chopper_data(chopper):
        """
        Extract radius, slit_height, and slit_edges data from a given chopper group.
        """
        radius = chopper["radius"][()]
        slit_height = chopper["slit_height"][()]
        slit_edges = chopper["slit_edges"][()]

        return radius, slit_height, slit_edges

    @staticmethod
    def find_x(radius, theta):
        return radius * np.cos(np.deg2rad(theta))

    @staticmethod
    def find_y(radius, theta):
        return radius * np.sin(np.deg2rad(theta))

    def create_point_set(self, radius, slit_height, slit_edge):

        outer_x = self.find_x(radius, slit_edge)
        outer_y = self.find_y(radius, slit_edge)

        print(outer_x)

        outer_front_point = Point(outer_x, outer_y, self.z)
        outer_back_point = Point(outer_x, outer_y, -self.z)

        inner_x = self.find_x(slit_height, slit_edge)
        inner_y = self.find_y(slit_height, slit_edge)

        inner_front_point = Point(inner_x, inner_y, self.z)
        inner_back_point = Point(inner_x, inner_y, -self.z)

        return outer_front_point, outer_back_point, inner_front_point, inner_back_point

    def generate_off_file(self, chopper):
        """
        Create an OFF file from a given chopper.
        """

        off_creator = OFFFileCreator()

        radius, slit_height, slit_edges = self.get_chopper_data(chopper)

        first_outer_front, first_outer_back, first_inner_front, first_inner_back = self.create_point_set(
            radius, slit_height, slit_edges[0]
        )

        # off_creator.add_vertex(Point(0,0,self.z))
        # off_creator.add_vertex(Point(0,0,-self.z))

        off_creator.add_vertex(first_outer_front)
        off_creator.add_vertex(first_outer_back)
        off_creator.add_vertex(first_inner_front)
        off_creator.add_vertex(first_inner_back)

        """
        off_creator.add_front_vertex(first_outer_front)
        off_creator.add_front_vertex(first_inner_front)
        off_creator.add_back_vertex(first_outer_back)
        off_creator.add_back_vertex(first_inner_back)
        """

        off_creator.add_face(
            [first_outer_front, first_outer_back, first_inner_back, first_inner_front]
        )

        prev_outer_front = first_outer_front
        prev_outer_back = first_outer_back
        prev_inner_front = first_inner_front
        prev_inner_back = first_inner_back

        for i in range(1, len(slit_edges)):

            current_outer_front, current_outer_back, current_inner_front, current_inner_back = self.create_point_set(
                radius, slit_height, slit_edges[i]
            )

            off_creator.add_vertex(current_outer_front)
            off_creator.add_vertex(current_outer_back)
            off_creator.add_vertex(current_inner_front)
            off_creator.add_vertex(current_inner_back)

            off_creator.add_face(
                [
                    current_outer_front,
                    current_outer_back,
                    current_inner_back,
                    current_inner_front,
                ]
            )

            if i % 2:
                off_creator.add_face(
                    [
                        prev_inner_front,
                        prev_inner_back,
                        current_inner_back,
                        current_inner_front,
                    ]
                )
                """
                off_creator.add_front_vertex(current_inner_front)
                off_creator.add_front_vertex(current_outer_front)
                off_creator.add_back_vertex(current_inner_back)
                off_creator.add_back_vertex(current_outer_back)
                """
            else:
                off_creator.add_face(
                    [
                        prev_outer_front,
                        prev_outer_back,
                        current_outer_back,
                        current_outer_front,
                    ]
                )
                """
                off_creator.add_front_vertex(current_outer_front)
                off_creator.add_front_vertex(current_inner_front)
                off_creator.add_back_vertex(current_outer_back)
                off_creator.add_back_vertex(current_inner_back)
                """
                off_creator.add_face(
                    [
                        prev_inner_front,
                        prev_outer_front,
                        current_outer_front,
                        current_inner_front,
                    ]
                )
                off_creator.add_face(
                    [
                        prev_inner_back,
                        prev_outer_back,
                        current_outer_back,
                        current_inner_back,
                    ]
                )

            prev_outer_front = current_outer_front
            prev_outer_back = current_outer_back
            prev_inner_front = current_inner_front
            prev_inner_back = current_inner_back

        off_creator.add_face(
            [
                current_outer_front,
                current_outer_back,
                first_outer_back,
                first_outer_front,
            ]
        )

        off_creator.add_face(
            [
                current_inner_front,
                current_outer_front,
                first_outer_front,
                first_inner_front,
            ]
        )
        off_creator.add_face(
            [current_inner_back, current_outer_back, first_outer_back, first_inner_back]
        )

        file = off_creator.create_file()
        print(file)

    def process(self):
        """
        Recipes need to implement this method and return information which
        is useful to a user and instructive to a person reading the code.
        See some of the recommended examples for inspiration what to return.

        :return: the essence of the information recorded in this feature
        """

        self.find_disk_choppers()

        if not self.choppers:
            return "Unable to find disk choppers."

        else:

            for chopper in self.choppers:
                self.generate_off_file(chopper)
