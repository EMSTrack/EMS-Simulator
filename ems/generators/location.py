import math
import random
from typing import List

import numpy as np
import yaml
from geopy import Point
from numpy.random import choice
from shapely import geometry
from shapely.ops import triangulate


# Interface for a location generator
class LocationGenerator:

    def generate(self, timestamp=None):
        raise NotImplementedError()


# Implementation for a location generator that randomly selects a point uniformly from a circle with given
# center and radius (in meters)
class CircleLocationGenerator(LocationGenerator):

    def __init__(self,
                 center_latitude: float,
                 center_longitude: float,
                 radius_km: float):
        self.center = Point(center_latitude, center_longitude)
        self.radius_km = radius_km
        self.radius_degrees = self.convert_radius(radius_km)

    def generate(self, timestamp=None):
        direction = random.uniform(0, 2 * math.pi)
        magnitude = self.radius_degrees * math.sqrt(random.uniform(0, 1))

        x = magnitude * math.cos(direction)
        y = magnitude * math.sin(direction)

        return Point(latitude=self.center.latitude + y,
                     longitude=self.center.longitude + x)

    def convert_radius(self, radius):
        km_in_one_degree = 110.54
        degrees = radius / km_in_one_degree
        return degrees


class PolygonLocationGenerator(LocationGenerator):

    def __init__(self,
                 vertices_longitude: List[float],
                 vertices_latitude: List[float],
                 ):
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
