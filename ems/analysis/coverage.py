from datetime import timedelta, datetime

from ems.analysis.metric import Metric
from ems.datasets.location import LocationSet
from ems.datasets.times import TravelTimes


# Computes a percent coverage given a radius
class PercentDoubleCoverage(Metric):
    """ """

    def __init__(self,
                 demands: LocationSet,
                 travel_times: TravelTimes,
                 r1: int = 600,
                 r2: int = 840,
                 tag=['primary_coverage', 'secondary_coverage']):
        super().__init__(tag=tag)
        self.demands = demands
        self.travel_times = travel_times
        self.r1 = timedelta(seconds=r1)
        self.r2 = timedelta(seconds=r2)

        # Caching for better performance
        self.primary_coverage_state = PercentCoverageState(ambulances=set(),
                                                           locations_coverage=[set() for _ in demands.locations])

        self.secondary_coverage_state = PercentCoverageState(ambulances=set(),
                                                             locations_coverage=[set() for _ in demands.locations])

    def calculate(self,
                  timestamp: datetime,
                  **kwargs):
        """ TODO """
        if "ambulances" not in kwargs:
            return None

        ambulances = kwargs["ambulances"]

        available_ambulances = [amb for amb in ambulances if not amb.deployed]

        ambulances_to_add = [a for a in available_ambulances if a not in self.primary_coverage_state.ambulances]
        ambulances_to_remove = [a for a in self.primary_coverage_state.ambulances if a not in available_ambulances]

        for ambulance in ambulances_to_add:
            self.add_ambulance_coverage(ambulance)

        for ambulance in ambulances_to_remove:
            self.remove_ambulance_coverage(ambulance)

        primary = 0
        for location_coverage in self.primary_coverage_state.locations_coverage:
            if len(location_coverage) > 0:
                primary += 1

        secondary = 0

        # Generate both the coverages # TODO update this comment if it's wrong
        for i in range(len(self.secondary_coverage_state.locations_coverage)):
            location_secondary_ambs = self.secondary_coverage_state.locations_coverage[i]
            location_primary_ambs = self.primary_coverage_state.locations_coverage[i]

            if len(location_primary_ambs) > 0:
                if len(location_secondary_ambs) > 0:

                    if len(location_primary_ambs) == 1:
                        if location_secondary_ambs != location_primary_ambs:
                            secondary += 1
                    else:
                        secondary += 1

        result = round(primary / len(self.demands) * 100, 4), round(secondary / len(self.demands) * 100, 4)
        return result

    def add_ambulance_coverage(self, ambulance):

        # Retrieve closest point from set 1 to the ambulance
        closest_to_amb, _, _ = self.travel_times.origins.closest(ambulance.location)

        for index, demand_loc in enumerate(self.demands.locations):

            # Retrieve closest point from set 2 to the demand
            closest_to_demand, _, _ = self.travel_times.destinations.closest(demand_loc)

            # Compute time and determine if less than r1
            if self.travel_times.get_time(closest_to_amb, closest_to_demand) < self.r1:
                self.primary_coverage_state.locations_coverage[index].add(ambulance)

            if self.travel_times.get_time(closest_to_amb, closest_to_demand) < self.r2:
                self.secondary_coverage_state.locations_coverage[index].add(ambulance)

        # Register ambulance as covering some area
        self.primary_coverage_state.ambulances.add(ambulance)
        self.secondary_coverage_state.ambulances.add(ambulance)

    def remove_ambulance_coverage(self, ambulance):

        for location_coverage in self.primary_coverage_state.locations_coverage:

            # Remove ambulance from covering the location
            if ambulance in location_coverage:
                location_coverage.remove(ambulance)

        # Unregister ambulance as covering some area
        self.primary_coverage_state.ambulances.remove(ambulance)

        for location_coverage in self.secondary_coverage_state.locations_coverage:

            # Remove ambulance from covering the location
            if ambulance in location_coverage:
                location_coverage.remove(ambulance)

        # Unregister ambulance as covering some area
        self.secondary_coverage_state.ambulances.remove(ambulance)


class PercentCoverageState:

    def __init__(self,
                 ambulances,
                 locations_coverage):
        self.ambulances = ambulances
        self.locations_coverage = locations_coverage


# Computes a percent coverage given a radius
class PercentCoverage(Metric):

    def __init__(self,
                 demands: LocationSet,
                 travel_times: TravelTimes,
                 r1: int = 600,
                 tag='percent_coverage'):
        super().__init__(tag=tag)
        self.demands = demands
        self.travel_times = travel_times
        self.r1 = timedelta(seconds=r1)

        # Caching for better performance
        self.coverage_state = PercentCoverageState(ambulances=set(),
                                                   locations_coverage=[set() for _ in demands.locations])

    def calculate(self,
                  timestamp: datetime,
                  **kwargs):

        if "ambulances" not in kwargs:
            return None

        ambulances = kwargs["ambulances"]

        available_ambulances = [amb for amb in ambulances if not amb.deployed]

        ambulances_to_add = [a for a in available_ambulances if a not in self.coverage_state.ambulances]
        ambulances_to_remove = [a for a in self.coverage_state.ambulances if a not in available_ambulances]

        for ambulance in ambulances_to_add:
            self._add_ambulance_coverage(ambulance)

        for ambulance in ambulances_to_remove:
            self._remove_ambulance_coverage(ambulance)

        sm = 0
        for location_coverage in self.coverage_state.locations_coverage:
            if len(location_coverage) > 0:
                sm += 1
        return sm / len(self.demands)

    def _add_ambulance_coverage(self, ambulance):

        # Retrieve closest point from set 1 to the ambulance
        closest_to_amb, _, _ = self.travel_times.origins.closest(ambulance.location)

        for index, demand_loc in enumerate(self.demands.locations):

            # Retrieve closest point from set 2 to the demand
            closest_to_demand, _, _ = self.travel_times.destinations.closest(demand_loc)

            # Compute time and determine if less than r1
            if self.travel_times.get_time(closest_to_amb, closest_to_demand) <= self.r1:
                self.coverage_state.locations_coverage[index].add(ambulance)

        # Register ambulance as covering some area
        self.coverage_state.ambulances.add(ambulance)

    def _remove_ambulance_coverage(self, ambulance):

        for location_coverage in self.coverage_state.locations_coverage:

            # Remove ambulance from covering the location
            if ambulance in location_coverage:
                location_coverage.remove(ambulance)

        # Unregister ambulance as covering some area
        self.coverage_state.ambulances.remove(ambulance)


# Computes a radius coverage
class RadiusCoverage(Metric):

    def __init__(self,
                 demands: LocationSet,
                 travel_times: TravelTimes,
                 percent: float = 85,
                 tag="radius_coverage"):
        super().__init__(tag)
        self.demands = demands
        self.travel_times = travel_times
        self.percent = percent

        # self.coverage_state = RadiusCoverageState(ambulances=[],
        #                                           tt_to_ambulance=[None for _ in demands.locations])

    def calculate(self,
                  timestamp: datetime,
                  **kwargs):

        if "ambulances" not in kwargs:
            return None

        ambulances = kwargs["ambulances"]

        # available_ambulances = [amb for amb in ambulances if not amb.deployed]
        #
        # ambulances_to_add = [a for a in available_ambulances if a not in self.coverage_state.ambulances]
        # ambulances_to_remove = [a for a in self.coverage_state.ambulances if a not in available_ambulances]

        # Snap ambulance location to closest location in loc_set_1
        ambulance_locations = [self.travel_times.origins.closest(ambulance.location)[0] for ambulance in ambulances if
                               not ambulance.deployed]

        if len(ambulance_locations) == 0:
            return -1

        # Snap demand location to closest location in loc_set_2
        demand_locations = [self.travel_times.destinations.closest(demand_location)[0] for demand_location in
                            self.demands.locations]

        min_tts = []

        # Find the travel time from each demand to the closest ambulance (aka minimum travel time)
        for demand_location in demand_locations:
            tt_to_ambulance = [self.travel_times.get_time(ambulance_location, demand_location) for ambulance_location in
                               ambulance_locations]
            min_tts.append(min(tt_to_ambulance))

        # Take the max of those travel times
        return max(min_tts).seconds
