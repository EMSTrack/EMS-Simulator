import random
from datetime import datetime
from datetime import timedelta
from itertools import combinations
from typing import List

from ems.analysis.coverage import PercentDoubleCoverage
from ems.datasets.times import TravelTimes
from ems.models.ambulance import Ambulance
from ems.models.case import Case


class AmbulanceSelector:
    """
    Defines a strategy for selecting an ambulance
    """

    def select(self,
               ambulances: List[Ambulance],
               case: Case,
               time: datetime):
        """

        :param ambulances: The ambulances to select from for dispatch
        :type ambulances: List<Ambulance>
        :param case: The case to select an ambulance for
        :type case: Case
        :param time: The time at which to select an ambulance
        :type time: datetime
        :return: The selected ambulance
        """
        raise NotImplementedError()


class BestTravelTime(AmbulanceSelector):
    """
    Selects the ambulance with the fastest travel time to the case location
    """

    # TODO - modify such that travel times are generated, instead of having travel times object dependency
    def __init__(self,
                 travel_times: TravelTimes = None):
        """
        :param travel_times: Travel times between locations
        :type travel_times: Travel times
        """
        self.travel_times = travel_times

    def select(self,
               ambulances: List[Ambulance],
               case: Case,
               time: datetime):

        # Compute the closest demand point to the case location
        loc_set_2 = self.travel_times.destinations
        closest_loc_to_case, _, _ = loc_set_2.closest(case.incident_location)

        # Select an ambulance to attend to the given case and obtain the its duration of travel
        chosen_ambulance, ambulance_travel_time = self._find_fastest_ambulance(
            ambulances, closest_loc_to_case)

        return chosen_ambulance

    # TODO -- refactor such that the travel times object/generator returns the times; rename params
    def _find_fastest_ambulance(self, ambulances, closest_loc_to_case):
        """
        Finds the ambulance with the shortest one way travel time from its base to the destination
        :param ambulances:
        :param closest_loc_to_case:
        :return: The selected ambulance and the travel time to the case
        """

        shortest_time = timedelta.max
        fastest_amb = None

        loc_set_1 = self.travel_times.origins

        for amb in ambulances:

            # Compute closest location in the first set to the ambulance
            ambulance_location = amb.location

            # Compute closest location in location set 1 to the ambulance location
            closest_loc_to_ambulance = loc_set_1.closest(ambulance_location)[0]

            # Compute the time from the location point mapped to the ambulance to the location point mapped to the case
            time = self.travel_times.get_time(closest_loc_to_ambulance, closest_loc_to_case)
            if shortest_time > time:
                shortest_time = time
                fastest_amb = amb

        if fastest_amb is not None:
            return fastest_amb, shortest_time

        return None, None


class LeastDisruption(BestTravelTime):
    """
    Selects the ambulance that disrupts coverage the least
    """

    # TODO -- rename, or repurpose algorithm such that "coverage" could be defined in any way
    def __init__(self,
                 travel_times: TravelTimes = None,
                 demands=None,
                 r1=600,
                 r2=840,):
        """
        :param travel_times: Travel times between locations
        :type travel_times:
        :param demands: Demands to cover
        :type demands:
        :param r1: R1 distance
        :type r1:
        :param r2: R2 distance
        :type r2:
        """
        self.travel_times = travel_times
        self.coverage = PercentDoubleCoverage(
            demands=demands,
            travel_times=self.travel_times,
            r1=r1,
            r2=r2,
        )
        super().__init__(travel_times=travel_times)

    def select(self,
               ambulances: List[Ambulance],
               case: Case,
               time: datetime):

        # Select an ambulance that disrupts the coverage the least regardless of travel time.
        chosen_ambulance, ambulance_travel_time = self._find_least_disruption(ambulances)
        return chosen_ambulance

    def _find_least_disruption(self, ambulances):
        """
        Finds the ambulance with the least disruption of coverage
        :param ambulances
        :return: The ambulance and the travel time
        """

        # Calculate all combinations of ambulances's coverage and return the best one.
        chosen_ambulance_set = []
        current_primary = -1
        current_secondary = -1

        potential_ambulances = list(combinations(ambulances, len(ambulances) - 1))

        # Primary coverage considered first. In the event of a tie, update the seconday coverage.
        for ambulance_set in potential_ambulances:
            primary, secondary = self.coverage.calculate(datetime.now(), ambulances=ambulance_set)

            # If the primary is larger, this clearly wins.
            if primary > current_primary:
                current_primary = primary
                current_secondary = secondary

                chosen_ambulance_set = ambulance_set

            # If the primaries are the same, then consider the larger of the secondaries.
            elif primary == current_primary:
                if secondary > current_secondary:
                    current_secondary = secondary
                    # TODO A future implementation of this would simply use a list and recursion.
                    chosen_ambulance_set = ambulance_set

        chosen_ambulance = [ambulance for ambulance in ambulances if ambulance not in chosen_ambulance_set][0]

        return chosen_ambulance, None


class OptimalTravelTimeWithCoverage(AmbulanceSelector):
    """
    Selects the ambulance that achieves the best ratio between best travel time and coverage, triaged by the
    case priority
    """

    # TODO -- rename, or repurpose algorithm such that "coverage" could be defined in any way
    def __init__(self,
                 travel_times: TravelTimes = None,
                 demands=None,
                 r1=600,
                 r2=840,
                 ):
        """
        :param travel_times: Travel times between locations
        :type travel_times:
        :param demands: Demands to cover
        :type demands:
        :param r1: R1 distance
        :type r1:
        :param r2: R2 distance
        :type r2:
        """
        self.travel_times = travel_times
        # This instance is used for calculating future coverages

        self.coverage = PercentDoubleCoverage(
            demands=demands,
            travel_times=self.travel_times,
            r1=r1,
            r2=r2,
        )

    def select(self,
               ambulances: List[Ambulance],
               case: Case,
               time: datetime,
               ):
        """
        Runs *both* of the ambulance selection policy algorithms and then runs a weight algorithm
        to scale between the two algorithms.
        """

        if not case.priority:
            case.priority = 3
            print("WARNING: Case priority was not found but optimal dispatching requires it. ")

        # Optimization: if priority is 1, send fastest ambulance. If it's 4, send best coverage.
        loc_set_2 = self.travel_times.destinations
        closest_loc_to_case, _, _ = loc_set_2.closest(case.incident_location)

        times = self._sort_ambulances_by_traveltime(ambulances, closest_loc_to_case)
        coverages = self._sort_ambulances_by_coverage(ambulances)

        # As times increase, it is less favorable than the fastest time. For example,
        # if t0 = 9 minutes and t1 = 10 minutes, then t1 is 9/10 or 90% favorable.
        # t0 is always favorable because t0/t0 = 100%.

        times_ranked = [(t[0].total_seconds(), t[1]) for t in times]
        times_ranked = [(times[0][0] / t[0], t[1]) for t in times]

        # Do the same thing with coverage. Divide each worse coverage by the best coverage
        # to get a < 100% score.

        best_cov = coverages[0][0]
        # Make the primary coverage worth 100x more than the secondary coverage.
        coverages_ranked = [((c[0][0] * 100 + c[0][1]) / (best_cov[0] * 100 + best_cov[1] + 0.0000001), c[1]) for c in
                            coverages]

        # We are only concerned about combining the same ambulance's travel time and coverage.
        # It is not useful to weigh together different ambulance's rankings. Hence the condition.
        priorities_applied = [(self._weighted_metrics2(t[0], c[0], case.priority), t[1]) \
                              for t in times_ranked for c in coverages_ranked if t[1] == c[1]]

        priorities_applied.sort(key=lambda t: t[0])
        priorities_applied.reverse()

        return priorities_applied[0][1]

    # This is Version 2 to weigh the two algorithms
    def _weighted_metrics2(self, time, coverage, priority):
        """ Weighted dispatch as ambulance selection policy, version 2. """

        # Amplifiers for each of the weights
        alpha = 3
        beta = 4

        # Calculate each term
        t = alpha * time * abs(4 - priority) / 3
        c = beta * coverage * abs(1 - priority) / 3

        score = t + c

        return score

    # These should be the same sorting algorithms as the previous two.
    def _sort_ambulances_by_traveltime(self, ambulances, closest_loc_to_case):
        """
        Finds the ambulance with the shortest one way travel time from its base to the
        demand point
        :param ambulances:
        :param closest_loc_to_case:
        :return: The ambulance and the travel time
        """

        loc_set_1 = self.travel_times.origins

        list_of_ambulances = []

        for amb in ambulances:
            # Compute closest location in the first set to the ambulance
            ambulance_location = amb.location

            # Compute closest location in location set 1 to the ambulance location
            closest_loc_to_ambulance = loc_set_1.closest(ambulance_location)[0]

            # Compute the time from the location point mapped to the ambulance to the location point mapped to the case
            time = self.travel_times.get_time(closest_loc_to_ambulance, closest_loc_to_case)

            list_of_ambulances.append(
                (time, amb)
            )

        # Sort by the travel time.
        list_of_ambulances.sort(key=lambda t: t[0])
        # list_of_ambulances.reverse()
        return list_of_ambulances

    # TODO CHANGE THIS TO SORT BY LEAST DISRUPTION
    def _sort_ambulances_by_coverage(self, ambulances):
        """ Calculate all combinations of ambulances's coverage and return the best one. """

        potential_ambulances = list(combinations(ambulances, len(ambulances) - 1))
        list_of_ambulances = []

        for ambulance_set in potential_ambulances:
            coverage = self.coverage.calculate(datetime.now(), ambulances=ambulance_set)
            list_of_ambulances.append(
                (coverage, [a for a in ambulances if a not in ambulance_set][0])
            )

        list_of_ambulances.sort(key=lambda t: t[0])
        list_of_ambulances.reverse()

        return list_of_ambulances


class RandomSelector(AmbulanceSelector):
    """
    Selects a random ambulance
    """
    def select(self,
               ambulances: List[Ambulance],
               case: Case,
               time: datetime):
        # Randomly select
        chosen_ambulance = random.sample(ambulances, 1)[0]

        return chosen_ambulance
