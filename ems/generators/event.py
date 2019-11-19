from datetime import datetime

from geopy import Point

from ems.algorithms.hospital import HospitalSelector
from ems.generators.duration import DurationGenerator
from ems.models.ambulance import Ambulance
from ems.models.event import EventType, Event


class EventGenerator:
    """
    Stochastically generates events for an emergency case
    """

    def __init__(self,
                 travel_duration_generator: DurationGenerator,
                 incident_duration_generator: DurationGenerator,
                 hospital_duration_generator: DurationGenerator,
                 hospital_selector: HospitalSelector):
        """
        :param travel_duration_generator: Generates travel times between a base and an emergency
        :type travel_duration_generator: DurationGenerator
        :param incident_duration_generator: Generates the time spent attending to a patient
        :type incident_duration_generator: DurationGenerator
        :param hospital_duration_generator: Generates the travel times between an emergency location and hospital
        :type hospital_duration_generator: DurationGenerator
        :param hospital_selector: Selects a hospital for patient transport
        :type hospital_selector: HospitalSelector
        """
        self.hospital_selector = hospital_selector
        self.hospital_duration_generator = hospital_duration_generator
        self.incident_duration_generator = incident_duration_generator
        self.travel_duration_generator = travel_duration_generator

    def generate(self,
                 ambulance: Ambulance,
                 incident_location: Point,
                 timestamp: datetime,
                 event_type: EventType,
                 hospital_location: Point=None):
        """
        Generates the next event for a given case based on the simulation parameters

        :param ambulance: Ambulance that is attending to the case
        :type ambulance: Ambulance
        :param incident_location: Location of the case emergency
        :type incident_location: Point
        :param timestamp: Current timestamp
        :type timestamp: datetime
        :param event_type: Type of the event to generate
        :type event_type: EventType
        :param hospital_location: Location of the hospital (can be None)
        :type hospital_location: Point
        :return:
        :rtype: Event
        """
        destination = None
        duration = 0

        if event_type == EventType.TO_INCIDENT:
            destination = incident_location
            duration = self.travel_duration_generator.generate(ambulance=ambulance,
                                                               destination=incident_location,
                                                               timestamp=timestamp)
        elif event_type == EventType.AT_INCIDENT:
            destination = incident_location
            duration = self.incident_duration_generator.generate(ambulance=ambulance,
                                                                 destination=incident_location,
                                                                 timestamp=timestamp)
        elif event_type == EventType.TO_BASE:
            destination = ambulance.base
            duration = self.travel_duration_generator.generate(ambulance=ambulance,
                                                               destination=destination,
                                                               timestamp=timestamp)

        elif event_type == EventType.TO_HOSPITAL or event_type == EventType.AT_HOSPITAL:

            if not hospital_location:
                destination = self.hospital_selector.select(timestamp=timestamp,
                                                            ambulance=ambulance)
            else:
                destination = hospital_location

            if event_type == EventType.TO_HOSPITAL:
                duration = self.travel_duration_generator.generate(ambulance=ambulance,
                                                                   destination=destination,
                                                                   timestamp=timestamp)
            else:
                duration = self.hospital_duration_generator.generate(ambulance=ambulance,
                                                                     destination=destination,
                                                                     timestamp=timestamp)
        else:
            # TODO -- other
            pass

        return Event(destination=destination,
                     duration=duration['duration'],
                     error=duration['error'] if 'error' in duration else None,
                     sim_dest=duration['sim_dest'] if 'sim_dest' in duration else None,
                     event_type=event_type)
