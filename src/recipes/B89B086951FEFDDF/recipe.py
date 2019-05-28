import h5py
import numpy as np


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
        return radius * np.cos(theta)

    @staticmethod
    def find_y(radius, theta):
        return radius * np.sin(theta)

    @staticmethod
    def create_point_string(x, y, z):
        return " ".join([str(x), str(y), str(z)]) + "\n"

    def generate_off_file(self, chopper):
        """
        Create an OFF file from a given chopper.
        """

        n_vertices = 0

        radius, slit_height, slit_edges = self.get_chopper_data(chopper)

        off_file = "OFF\n"

        off_points = ""

        front_outer_points = []
        back_outer_points = []

        front_inner_points = []
        back_inner_points = []

        for slit_edge in slit_edges:

            x = self.find_x(radius, slit_edge)
            y = self.find_x(radius, slit_edge)

            front_outer_points += [self.create_point_string(x, y, self.z)]
            back_outer_points += [self.create_point_string(x, y, -self.z)]

            x = self.find_x(slit_height, slit_edge)
            y = self.find_x(slit_height, slit_edge)

            front_inner_points += [self.create_point_string(x, y, self.z)]
            back_inner_points += [self.create_point_string(x, y, -self.z)]

            n_vertices += 4

            off_points += (
                front_outer_points[-1]
                + back_outer_points[-1]
                + front_inner_points[-1]
                + back_inner_points[-1]
            )

        off_file += str(len(front_outer_points)) + " 0 0\n" + off_points
        print(off_file)

        return off_file

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
