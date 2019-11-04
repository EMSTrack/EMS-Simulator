from typing import List

import pandas as pd
from geopy import Point
from scipy.spatial import KDTree

from ems.generators.location import LocationGenerator


# TODO -- Remove KD Tree functionality from base location set
class LocationSet:

    def __init__(self,
                 latitudes: List[float],
                 longitudes: List[float]):
        self.locations = [Point(latitude=latitude, longitude=longitude)
                          for latitude, longitude in zip(latitudes, longitudes)]
        self.kd_tree = self._initialize_kd_tree()

    def __len__(self):
        return len(self.locations)

    def __iter__(self):
        return iter(self.locations)

    def __getitem__(self, item):
        return self.locations[item]

    def closest(self, point: Point):
        """
        Finds the closest point in the corresponding generic list.
        For example, find the closest base given a GPS location.
        :param point:
        :return: The closest point and its index
        """

        # Query kd tree for nearest neighbor
        closest_point_data = self.kd_tree.query((point.longitude, point.latitude))

        # Retrieve closest point, its index, and the distance to it
        closest_point_ind = closest_point_data[1]
        closest_point = self.locations[closest_point_ind]
        closest_point_distance = closest_point_data[0]

        return closest_point, closest_point_ind, closest_point_distance

    def _initialize_kd_tree(self):
        """
        Initialize the kd_tree.
        Helper Method.
        :return:
        """

        # Form a kd-tree with the given list of locations
        points = [(loc.longitude, loc.latitude) for loc in self.locations]
        kd_tree = KDTree(points)
        return kd_tree

    def write_to_file(self, output_filename: str):
        a = [{"latitude": location.latitude,
              "longitude": location.longitude} for location in self.locations]
        df = pd.DataFrame(a, columns=["latitude", "longitude"])
        df.to_csv(output_filename, index=False)


class KDTreeLocationSet(LocationSet):

    def __init__(self,
                 latitudes: List[float],
                 longitudes: List[float]):
        super().__init__(latitudes, longitudes)
        self.kd_tree = self._initialize_kd_tree()

    def _initialize_kd_tree(self):
        """
        Initialize the kd_tree.
        Helper Method.
        :return:
        """

        # Form a kd-tree with the given list of locations
        points = [(loc.longitude, loc.latitude) for loc in self.locations]
        kd_tree = KDTree(points)
        return kd_tree

    def closest(self, point: Point):
        """
        Finds the closest point in the corresponding generic list.
        For example, find the closest base given a GPS location.
        :param point:
        :return: The closest point and its index
        """

        # Query kd tree for nearest neighbor
        closest_point_data = self.kd_tree.query((point.longitude, point.latitude))

        # Retrieve closest point, its index, and the distance to it
        closest_point_ind = closest_point_data[1]
        closest_point = self.locations[closest_point_ind]
        closest_point_distance = closest_point_data[0]

        return closest_point, closest_point_ind, closest_point_distance


class RandomLocationSet(KDTreeLocationSet):

    def __init__(self,
                 count: int,
                 generator: LocationGenerator):
        self.count = count
        self.generator = generator
        latitudes, longitudes = self.generate_locations()
        super().__init__(latitudes, longitudes)

    def generate_locations(self):
        locations = [self.generator.generate() for _ in range(self.count)]
        latitudes = [l.latitude for l in locations]
        longitudes = [l.longitude for l in locations]
        return latitudes, longitudes
