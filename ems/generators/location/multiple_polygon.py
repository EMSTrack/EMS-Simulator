from numpy.random import choice
from typing import List
import yaml

from ems.generators.location.location import LocationGenerator
from ems.generators.location.polygon import PolygonLocationGenerator


class MultiPolygonLocationGenerator(LocationGenerator):
    """
    A region is divided into a set of regions so that the region can simulate certain zones
    having more cases occurring than others.
    """

    def __init__(self,
                 longitudes: List[List[float]] = None,
                 latitudes: List[List[float]] = None,
                 longitudes_file: str = None,
                 latitudes_file: str = None,
                 densities: List[float] = None):
        """
        Asserts correct assumptions about multi-polygon, like sum(probabilities) = 100 %
        :param polygons: Set of polygons denoted as a list of list of points.
        :param densities: The probability for each polygon respectively to each polygon.
        """

        if not any([latitudes and longitudes, longitudes_file and latitudes_file]):
            raise Exception("No polygon coordinates specified")

        if not longitudes:
            with open(longitudes_file, 'r') as lons_file:
                longitudes = yaml.load(lons_file)

        if not latitudes:
            with open(latitudes_file, 'r') as lats_file:
                latitudes = yaml.load(lats_file)

        # Set densities
        if densities is None:
            self.densities = [1 / len(longitudes) for _ in longitudes]
        else:
            self.densities = densities

        # Validate function args
        if sum(densities) != 1.0:
            raise Exception("Sum of densities should add up to 100%")
        if len(densities) != len(longitudes):
            raise Exception("Provided polygons and densities are not equal in length")

        # self.polygon_generators = self.create_generators(each_polygons_longitudes, each_polygons_latitudes)
        self.polygon_generators = [PolygonLocationGenerator(longitudes[i], latitudes[i])
                                   for i in range(len(longitudes))]

    def generate(self, timestamp=None):
        """
        Choose a polygon based on the probability distribution.

        :param timestamp: The time at which this case starts
        :return:
        """
        generator = choice(self.polygon_generators, 1, p=self.densities)[0]
        return generator.generate(timestamp)
