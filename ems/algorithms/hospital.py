import random
from datetime import datetime
from datetime import timedelta

from ems.datasets.location import LocationSet
from ems.datasets.times import TravelTimes
from ems.models.ambulance import Ambulance


class HospitalSelector:
    """
    Defines a strategy for selecting a hospital
    """

    def select(self,
               timestamp: datetime,
               ambulance: Ambulance):
        """
        Selects a hospital

        :param timestamp: Timestamp of selection
        :type timestamp: datetime
        :param ambulance: The ambulance that will travel to the hospital
        :type ambulance: Ambulance
        :return: The selected hospital
        """
        raise NotImplementedError()


class RandomHospitalSelector(HospitalSelector):
    """
    Randomly selects a hospital
    """

    def __init__(self, hospital_set: LocationSet):
        """
        :param hospital_set: The hospitals to select from
        :type hospital_set: HospitalSet
        """
        self.hospital_set = hospital_set

    def select(self, timestamp: datetime, ambulance: Ambulance):
        return random.choice(self.hospital_set.locations)


# TODO -- remove dependency on travel times, or convert TravelTimes to be an interface
class FastestHospitalSelector(HospitalSelector):
    """
    Selects the hospital the given ambulance will reach the fastest
    """

    def __init__(self,
                 hospital_set: LocationSet,
                 travel_times: TravelTimes):
        """
        :param hospital_set: The hospitals to select from
        :type hospital_set: HospitalSet
        :param travel_times: The travel times between locations
        :type travel_times: TravelTimes
        """
        self.hospital_set = hospital_set
        self.travel_times = travel_times

    def select(self,
               timestamp: datetime,
               ambulance: Ambulance):

        # Compute the closest point in set 2 to the ambulance
        loc_set_1 = self.travel_times.origins
        closest_loc_to_ambulance, _, _ = loc_set_1.closest(ambulance.location)

        # Select an ambulance to attend to the given case and obtain the its duration of travel
        chosen_hospital, travel_time = self._find_fastest_hospital(closest_loc_to_ambulance)

        return chosen_hospital

    def _find_fastest_hospital(self, location):

        shortest_time = timedelta.max
        fastest_hosp = None

        loc_set_2 = self.travel_times.destinations

        for hospital_location in self.hospital_set.locations:

            # Compute closest location in location set 2 to the hospital
            closest_loc_to_hospital = loc_set_2.closest(hospital_location)[0]

            # Compute the time from the location point mapped to the ambulance
            # to the location point mapped to the hospital
            time = self.travel_times.get_time(location, closest_loc_to_hospital)

            if shortest_time > time:
                shortest_time = time
                fastest_hosp = hospital_location

        return fastest_hosp, shortest_time
