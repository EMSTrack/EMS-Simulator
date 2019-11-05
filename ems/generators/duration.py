import math
import random
from datetime import datetime, timedelta

from geopy import Point
from geopy.distance import distance

from ems.datasets.times import TravelTimes
from ems.models.ambulance import Ambulance


# Interface for generating event durations
class DurationGenerator:

    # TODO -- use kwargs to support generation of durations w/o ambulance and destination
    def generate(self,
                 ambulance: Ambulance = None,
                 destination: Point = None,
                 timestamp: datetime = None):
        raise NotImplementedError()


class DistanceDurationGenerator(DurationGenerator):

    def __init__(self, velocity):
        self.velocity = velocity

    def generate(self,
                 ambulance: Ambulance = None,
                 destination: Point = None,
                 timestamp: datetime = None):
        distance_km = distance(ambulance.location, destination).km
        return {'duration': timedelta(seconds=int(distance_km / self.velocity))}


class ConstantDurationGenerator(DurationGenerator):

    def __init__(self, constant: timedelta):
        self.constant = constant

    def generate(self,
                 ambulance: Ambulance = None,
                 destination: Point = None,
                 timestamp: datetime = None):
        return {'duration': self.constant}


# Implementation for a duration generator, where duration until next incident is drawn from the exponential
# distribution with parameter lambda
# lambda = (total # of cases) / (total # of time units in an interval)
# e.g. For 1,000 cases in 40,000 minutes, lambda = 1/40
class PoissonDurationGenerator(DurationGenerator):

    def __init__(self,
                 lmda: float):
        self.lmda = lmda

    def generate(self,
                 ambulance: Ambulance = None,
                 destination: Point = None,
                 timestamp: datetime = None):
        rand = -math.log(1.0 - random.random())
        minutes_until_next = rand / self.lmda
        return {'duration': timedelta(minutes=minutes_until_next)}


# Implementation of an event duration generator that uniformly selects a random duration between two bounds
class RandomDurationGenerator(DurationGenerator):

    def __init__(self,
                 lower_bound: float = 5,
                 upper_bound: float = 20):
        self.lower_bound = timedelta(minutes=lower_bound)
        self.upper_bound = timedelta(minutes=upper_bound)

    def generate(self,
                 ambulance: Ambulance = None,
                 destination: Point = None,
                 timestamp: datetime = None):
        seconds_lower_bound = self.lower_bound.total_seconds()
        seconds_upper_bound = self.upper_bound.total_seconds()

        duration_in_seconds = random.randint(seconds_lower_bound, seconds_upper_bound)

        return {'duration': timedelta(seconds=duration_in_seconds)}


class TravelTimeDurationGenerator(DurationGenerator):

    def __init__(self,
                 travel_times: TravelTimes,
                 epsilon: float):
        self.travel_times = travel_times
        self.epsilon = epsilon

    def generate(self,
                 ambulance: Ambulance = None,
                 destination: Point = None,
                 timestamp: datetime = None):
        # Compute the point from first location set to the ambulance location
        loc_set_1 = self.travel_times.origins
        closest_loc_to_orig, _, _ = loc_set_1.closest(ambulance.location)

        # Compute the point from the second location set to the destination
        loc_set_2 = self.travel_times.destinations
        closest_loc_to_dest, _, _ = loc_set_2.closest(destination)

        # Calculate the error as a percentage between the sim dist and the real dist
        sim_dist = distance(closest_loc_to_dest, closest_loc_to_orig)
        real_dist = distance(destination, ambulance.location)
        difference = 100 * ((sim_dist.feet - real_dist.feet) * real_dist.feet) / (
                    math.pow(real_dist.feet, 2) + self.epsilon)

        # Return time lookup
        return {'duration': self.travel_times.get_time(closest_loc_to_orig, closest_loc_to_dest),
                'error': difference,
                'sim_dest': closest_loc_to_dest}
