# The following functions define default algorithms for the DispatchAlgorithm class.
from datetime import timedelta
from typing import List

import geopy
import geopy.distance
import numpy as np

from scipy.spatial import KDTree

from ems.algorithms.algorithm import Algorithm
from ems.data.traveltimes import TravelTimes
from ems.models.ambulance import Ambulance
from ems.models.case import Case
from ems.models.demand import Demand


# An implementation of a "fastest travel time" algorithm from a base to
# the demand point closest to a case

class DispatcherAlgorithm(Algorithm):

    def __init__(self,
                 traveltimes: TravelTimes = None):
        self.traveltimes = traveltimes

    def select_ambulance(self,
                         ambulances: List[Ambulance],
                         case: Case,
                         demands: List[Demand]):

        # Compute the closest demand point to the case location
        closest_demand = self.closest_distance(demands, case.location)

        # Select an ambulance to attend to the given case and obtain the its duration of travel
        chosen_ambulance, ambulance_travel_time = self.find_fastest_ambulance(
            ambulances, self.traveltimes, closest_demand)

        return chosen_ambulance, ambulance_travel_time

    def closest_distance(self, list_type, target_point):
        """
        Finds the closest point in the corresponding generic list.
        For example, find the closest base given a GPS location.
        :param list_type:
        :param target_point:
        :return: the position in that list
        """

        # Compute differences between target point and each element's location in list type
        differences = [geopy.distance.vincenty(target_point, element.location).km for element in list_type]

        # Find the index of the minimum difference and return the element at that index
        min_index = np.argmin(differences)
        return list_type[min_index]

    def find_fastest_ambulance(self, ambulances, traveltimes, demand):
        """
        Finds the ambulance with the shortest one way travel time from its base to the
        demand point
        :param ambulances:
        :param traveltimes:
        :param demand:
        :return: The ambulance and the travel time
        """

        shortest_time = timedelta(hours=9999999)
        fastest_amb = None

        for amb in ambulances:
            if not amb.deployed:
                time = self.find_traveltime(traveltimes, amb.base, demand)
                if shortest_time > time:
                    shortest_time = time
                    fastest_amb = amb

        if fastest_amb is not None:
            return fastest_amb, shortest_time

        return None, None

    def find_traveltime(self, traveltimes, base, demand):
        """
        Takes the travel time mapping, starting base, and ending demand to find time.
        :param base:
        :param demand:
        :return travel time:
        """

        # base should be a base object
        # demand should be a demand object

        return traveltimes.get_time(base, demand)
