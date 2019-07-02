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
    Tool for creating OFF files in the form of strings from NXdisk_chopper information.
    """

    def __init__(self, z):

        self.file_contents = "OFF\n"
        self.points = []
        self.faces = []
        self.z = z

        # Create points for the front and back centres of the disk
        self.front_centre = Point(0, 0, self.z)
        self.back_centre = Point(0, 0, -self.z)

        # Add the front and back centre points to the lists of points
        self.add_point_to_list(self.front_centre)
        self.add_point_to_list(self.back_centre)

    @staticmethod
    def polar_to_cartesian_2d(r, theta):
        """
        Converts polar coordinates to cartesian coordinates.
        :param r: The vector magnitude.
        :param theta: The vector angle.
        :return: x, y
        """
        return r * np.cos(theta), r * np.sin(theta)

    def create_mirrored_points(self, r, theta):
        """
        Creates two points that share the same x and y values and have opposite z values.
        :param r: The distance between the points and the front/back centre of the disk chopper.
        :param theta: The angle between the point and the front/back centre.
        :return: Two points that have a distance of 2*z from each other.
        """
        x, y = self.polar_to_cartesian_2d(r, theta)

        return Point(x, y, self.z), Point(x, y, -self.z)

    def create_and_add_point_set(self, radius, centre_to_slit_start, slit_edge):
        """
        Creates and records the upper and lower points for a slit edge and adds these to the file string. Also adds the
        face made from all four points to the file string.
        :param radius: The radius of the disk chopper.
        :param centre_to_slit_start: The distance between the disk centre and the start of the slit.
        :param slit_edge: The angle of the slit in radians.
        :return: A list containing point objects for the four points in the chopper mesh with an angle of `slit_edge`.
        """

        # Create the upper and lower points for the opening/closing slit edge.
        upper_front_point, upper_back_point = self.create_mirrored_points(
            radius, slit_edge
        )
        lower_front_point, lower_back_point = self.create_mirrored_points(
            centre_to_slit_start, slit_edge
        )

        # Add all of the points to the list of points.
        self.add_point_to_list(upper_front_point)
        self.add_point_to_list(upper_back_point)
        self.add_point_to_list(lower_front_point)
        self.add_point_to_list(lower_back_point)

        # Create a face for the slit edge that contains all four points.
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
        Creates and records two mirrored points and adds these to the list of points.
        :param r: The distance between the point and front/back centre of the disk chopper.
        :param theta: The angle between the point and the front/back centre.
        :return: The two point objects.
        """

        front, back = self.create_mirrored_points(r, theta)
        self.add_point_to_list(front)
        self.add_point_to_list(back)

        return front, back

    def add_face_connected_to_front_centre(self, points):
        """
        Records a face that is connected to the center point on the front of the disk chopper.
        :param points: A list of points that make up the face minus the centre point.
        """
        self.add_face_to_list([self.front_centre] + points)

    def add_face_connected_to_back_centre(self, points):
        """
        Records a face that is connected to the center point on the back of the disk chopper.
        :param points: A list of points that make up the face minus the centre point.
        """
        self.add_face_to_list([self.back_centre] + points)

    def add_point_to_list(self, point):
        """
        Records a point and gives it an ID.
        :param point: The point that is added to the list of points.
        """
        point.set_id(len(self.points))
        self.points.append(point)

    def add_face_to_list(self, points):
        """
        Records a face by creating a list of its point IDs and adding this to `self.faces`.
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

    def add_point_to_file_string(self, point):
        """
        Adds a point to the OFF file string by obtaining its point string.
        :param point: The point that is added to the file string.
        """
        self.file_contents += point.point_string()

    def add_face_to_file_string(self, face):
        """
        Adds a face to the OFF file string using a list of the point IDs.
        :param face: A list of the IDs of the points that make the face.
        """
        n_points = len(face)
        self.add_number_string_to_file_string([n_points] + face)

    def generate_file_contents(self):
        """
        Create the string that stores all the information needed in the OFF file.
        """
        n_points = len(self.points)
        n_faces = len(self.faces)

        # Add point count and face count to the file. Use zero for the number of edges as this is optional.
        self.add_number_string_to_file_string([n_points, n_faces, 0])

        # Add the point information to the string
        for point in self.points:
            self.add_point_to_file_string(point)

        # Add the face information to the string
        for face in self.faces:
            self.add_face_to_file_string(face)

    def get_file_contents(self):
        """
        :return An OFF file for a disk chopper in the form of a string.
        """
        return self.file_contents


class OFFFileWrapper(object):
    """
    Wrapper for an OFF file that is capable of writing files. Automatically gives it a name based on the the number of
    wrappers that have been created. Percent covered is rounded to a whole number.
    :param contents: A string containing the contents of the OFF file.
    :param percent_covered: Figure indicating how much of the chopper is covered by slits.
    :param num_slits: The number of slits in the chopper.
    """

    def __init__(self, name, contents, percent_covered, num_slits):

        self.name = name
        self.file_contents = contents
        self.percent_covered = int(round(percent_covered))
        self.num_slits = num_slits

    def set_name(self, name):
        """
        Change the name of the disk chopper.
        :param name: The desired name for the chopper.
        """
        self.name = name

    def str(self):
        """
        Prints a string containing the chopper name, its number of slits, and a figure indicating how much of the
        chopper is covered in slits.
        """
        print(
            "Chopper ({}) has {} openings covering {}% of the disk.".format(
                self.name, self.num_slits, self.percent_covered
            )
        )

    def write_OFF_file(self, filename):
        """
        Takes a filename argument and writes the `file_contents` to a file.
        :param filename: The desired filename of the OFF file.
        """
        with open(filename, "w") as f:
            f.write(self.file_contents)


class _NXDiskChopperFinder(object):
    """
    Finds disk chopper information in a NeXus file.
    """

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
    Generate OFF files from the NXdisk_choppers that are present in a NeXus file.

    Proposed by: dolica.akello-egwel@stfc.ac.uk
    """

    TWO_PI = np.pi * 2

    def __init__(self, filedesc, entrypath):
        """
        Recipes are required to set a descriptive self.title

        :param filedesc: h5py file object of the NeXus/HDF5 file
        :param entrypath: path of the entry containing this feature
        """

        self.file = filedesc
        self.entry = entrypath
        self.title = (
            "Create an OFF file from an NXdisk_chopper. Mesh resolution and thickness can be modified by changing"
            " the values in the recipe __init__ method."
        )

        self.choppers = None

        """
        Number of "slices" in the chopper excluding slit boundaries. Must be zero or greater. A higher value makes the
        mesh more detailed.
        """
        self.resolution = 50
        self.resolution_angles = None

        # The thickness of the disk chopper. This is used only for display purposes in order to make the model 3D.
        self.thickness = 50

    @staticmethod
    def get_chopper_data(chopper):
        """
        Extract radius, slit_height, slit_edges, and angle units data from a given chopper group.
        """
        name = chopper["name"][()]
        radius = chopper["radius"][()]
        slit_height = chopper["slit_height"][()]
        slit_edges = chopper["slit_edges"][()]
        units = chopper["slit_edges"].attrs["units"]

        return name, radius, slit_height, slit_edges, units

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
        """
        Create additional points and faces between the slit edges to make the mesh look smoother.
        :param off_creator: An OFFFileCreator object.
        :param first_angle: The angle of the first slit edge in radians.
        :param second_angle: The angle of the second slit edge in radians.
        :param first_front: The front point of the first slit edge,
        :param first_back: The back point of the first slit edge.
        :param second_front: The front point of the second slit edge.
        :param second_back: The back point of the second slit edge.
        :param r: The distance between the intermediate points and the back/front centre.
        """

        # Slice the array to obtain an array of intermediate angles between the two slit edges.
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

            # Create the front and back points
            current_front, current_back = off_creator.create_and_add_mirrored_points(
                r, angle
            )

            # Create a four-point face with the current points and the previous points
            off_creator.add_face_to_list(
                [prev_front, prev_back, current_back, current_front]
            )

            # Create a three-point face with the two front points and the front centre point
            off_creator.add_face_connected_to_front_centre([prev_front, current_front])

            # Create a three-point face with the two back points and the back centre point
            off_creator.add_face_connected_to_back_centre([prev_back, current_back])
            prev_front = current_front
            prev_back = current_back

        # Create a four-point face that connects the previous two points and the points from the second slit edge
        off_creator.add_face_to_list([prev_front, prev_back, second_back, second_front])

        # Create the final faces connected to the front and back centre points
        off_creator.add_face_connected_to_front_centre([prev_front, second_front])
        off_creator.add_face_connected_to_back_centre([prev_back, second_back])

    def generate_off_wrapper(self, chopper):
        """
        Create an OFF file from a given chopper and user-defined thickness and resolution values.
        """
        # Obtain the radius, slit height, slit angles, and units from the chopper data
        name, radius, slit_height, slit_edges, units = self.get_chopper_data(chopper)

        # Find the distance from the disk centre to the bottom of the slit
        centre_to_slit_bottom = radius - slit_height

        # Convert the slit edges to radians if they're in degrees
        if units == b"deg":
            slit_edges = [np.deg2rad(x) % recipe.TWO_PI for x in slit_edges]
        else:
            slit_edges = [x % recipe.TWO_PI for x in slit_edges]

        off_creator = OFFFileCreator(self.thickness * 0.5)

        # Create four points for the first slit in the chopper data
        point_set = off_creator.create_and_add_point_set(
            radius, centre_to_slit_bottom, slit_edges[0]
        )

        prev_upper_front = first_upper_front = point_set[0]
        prev_upper_back = first_upper_back = point_set[1]
        prev_lower_front = point_set[2]
        prev_lower_back = point_set[3]

        # Remove the first angle to avoid creating duplicate points at angle 0 and angle 360
        self.resolution_angles = np.linspace(0, recipe.TWO_PI, self.resolution + 1)[1:]

        for i in range(1, len(slit_edges)):

            # Create four points for the current slit edge
            current_upper_front, current_upper_back, current_lower_front, current_lower_back = off_creator.create_and_add_point_set(
                radius, centre_to_slit_bottom, slit_edges[i]
            )

            # Create lower intermediate points/faces if the slit angle index is odd
            if i % 2:
                self.create_intermediate_points_and_faces(
                    off_creator,
                    slit_edges[i - 1],
                    slit_edges[i],
                    prev_lower_front,
                    prev_lower_back,
                    current_lower_front,
                    current_lower_back,
                    centre_to_slit_bottom,
                )
            # Create upper intermediate points/faces if the slit angle index is even
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

        # Create intermediate points/faces between the first and last slit edges
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

        off_creator.generate_file_contents()

        return OFFFileWrapper(
            name,
            off_creator.get_file_contents(),
            self.find_percent_covered(slit_edges),
            len(slit_edges) // 2,
        )

    def find_percent_covered(self, slit_edges):
        """
        Determines the percentage of the chopper that is covered by slits.
        :param slit_edges: The array of slit-edge angles.
        :return: The percentage of slit coverage in the form of a float.
        """
        percent_covered = 0
        for i in range(0, len(slit_edges) - 1, 2):
            slit_size = (slit_edges[i + 1] - slit_edges[i]) % recipe.TWO_PI
            percent_covered += self.angle_to_percentage(slit_size)
        return percent_covered

    def process(self):
        """
        Recipes need to implement this method and return information which
        is useful to a user and instructive to a person reading the code.
        See some of the recommended examples for inspiration what to return.

        :return: A list of the the filenames of the OFF files that have been created.
        """

        chopper_finder = _NXDiskChopperFinder()
        self.choppers = chopper_finder.get_NXdisk_chopper(self.file, self.entry)

        required_fields = ["slit_height", "slit_edges", "radius"]
        required_attributes = [("slit_edges", "units")]

        if not self.choppers:
            raise Exception("No chopper data found in the NeXus file.")

        else:
            off_wrappers = []

            for chopper in self.choppers:

                self.validate_chopper(chopper, required_fields, required_attributes)
                off_wrappers.append(self.generate_off_wrapper(chopper))
                off_wrappers[-1].str()

            return off_wrappers

    @staticmethod
    def validate_chopper(chopper, required_fields, required_attributes):
        fails = []
        for field in required_fields:
            try:
                chopper[field][()]
            except KeyError:
                fails.append("{} is missing from chopper data.".format(field))

        for field, attr in required_attributes:
            try:
                chopper[field].attrs[attr]
            except KeyError:
                fails.append("{} is missing from {}.".format(attr, field))

        if len(fails) > 0:
            raise Exception("\n".join(fails))

    @staticmethod
    def angle_to_percentage(slit_size):
        """
        :param slit_size: The size of a slit in radians.
        :return: The slit size as a percentage of two pi.
        """
        return (slit_size / recipe.TWO_PI) * 100
