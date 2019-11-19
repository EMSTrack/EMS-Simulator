import math
import random
from typing import List

import numpy as np
import yaml
from geopy import Point
from numpy.random import choice
from shapely import geometry
from shapely.ops import triangulate


class LocationGenerator:
    """
    Generates a location
    """

    def generate(self, timestamp=None):
        """
        Generates a location

        :param timestamp: Optionally provide a time to vary location generation
        :type timestamp: datetime
        :return: A point
        :rtype: Point
        """
        raise NotImplementedError()


# Implementation for a location generator that randomly selects a point uniformly from a circle with given
# center and radius (in meters)
class CircleLocationGenerator(LocationGenerator):
    """
    Generates a location according to a uniform distribution within a circular area
    """

    # TODO -- rename radius_km
    def __init__(self,
                 center_latitude: float,
                 center_longitude: float,
                 radius_km: float):
        """
        :param center_latitude: Center latitude of the circle
        :type center_latitude: float
        :param center_longitude: Center longitude of the circle
        :type center_longitude: float
        :param radius_km: Radius in km of the circular area
        :type radius_km: float
        """
        self.center = Point(center_latitude, center_longitude)
        self.radius_km = radius_km
        self.radius_degrees = self._convert_radius(radius_km)

    def generate(self, timestamp=None):
        """
        Generates a uniformly distributed location within a circular area

        :param timestamp:
        :type timestamp: datetime
        :return: A point
        :rtype: Point
        """
        direction = random.uniform(0, 2 * math.pi)
        magnitude = self.radius_degrees * math.sqrt(random.uniform(0, 1))

        x = magnitude * math.cos(direction)
        y = magnitude * math.sin(direction)

        return Point(latitude=self.center.latitude + y,
                     longitude=self.center.longitude + x)

    def _convert_radius(self, radius):
        km_in_one_degree = 110.54
        degrees = radius / km_in_one_degree
        return degrees


class PolygonLocationGenerator(LocationGenerator):
    """
    Generates a location according to a uniform distribution within a polygon
    """

    def __init__(self,
                 vertices_longitude: List[float],
                 vertices_latitude: List[float],
                 ):
        """
        :param vertices_longitude: Vertices' longitudes of the polygon
        :type vertices_longitude: List<float>
        :param vertices_latitude: Vertices' latitudes of the polygon
        :type vertices_latitude: List<float>
        """
        self.vertices_latitude = vertices_latitude
        self.vertices_longitude = vertices_longitude
        self.polygon = geometry.Polygon([(latitude, longitude) for latitude, longitude in
                                         zip(vertices_latitude, vertices_longitude)])

    def generate(self, timestamp=None):
        triangles = triangulate(self.polygon)
        areas = [triangle.area for triangle in triangles]
        areas_normalized = [triangle.area / sum(areas) for triangle in triangles]

        t = np.random.choice(triangles, p=areas_normalized)
        a, b = sorted([random.random(), random.random()])

        coords = t.exterior.coords

        lat = a * coords[0][0] + (b - a) * coords[1][0] + (1 - b) * coords[2][0]
        long = a * coords[0][1] + (b - a) * coords[1][1] + (1 - b) * coords[2][1]

        return Point(latitude=lat, longitude=long)


# TODO -- should just input a list of polygon location generators!
class MultiPolygonLocationGenerator(LocationGenerator):
    """
    Defines a set of polygon slices, each with their own density of cases. First the generator samples a slice
    randomly according to the provided densities. Then it randomly samples a location within that polygon. This
    generator aims to provide functionality for modeling complex emergency location distributions
    """

    def __init__(self,
                 longitudes: List[List[float]] = None,
                 latitudes: List[List[float]] = None,
                 longitudes_file: str = None,
                 latitudes_file: str = None,
                 densities: List[float] = None):
        """
        Takes as input a list of list of points. The inner list determines the points of a specific polygon. The
        outer list determines the polygons for each slice of the region. Alternatively, these points can be defined
        in a separate file.

        Sum of densities must be equal to 100%

        :param longitudes: List of list of point longitudes
        :type longitudes: List<List<float>>
        :param latitudes: List of list of point latitudes
        :type latitudes: List<List<float>>
        :param longitudes_file: Filename containing point longitudes
        :type longitudes_file: string
        :param latitudes_file: Filename containing point latitudes
        :type latitudes_file: string
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
        Generates a time based on a multipolygon distribution. First the generator samples a polygon randomly according
        to the provided densities. Then it randomly samples a location within that polygon.

        :param timestamp: Optionally provide a time to vary location generation
        :type timestamp: datetime
        :return: A point
        :rtype: Point
        """
        generator = choice(self.polygon_generators, 1, p=self.densities)[0]
        return generator.generate(timestamp)
