from datetime import datetime
from typing import List

from geopy import Point

from ems.generators.event import EventGenerator
from ems.models.event import EventType, Event


class Case:

    # Include events
    def __init__(self,
                 id: int,
                 date_recorded: datetime,
                 incident_location: Point,
                 priority: float = None):
        self.id = id
        self.date_recorded = date_recorded
        self.incident_location = incident_location
        self.priority = priority

    def iterator(self, ambulance, current_time):
        raise NotImplementedError()

    def __lt__(self, other):
        return self.date_recorded < other.date_recorded

    def __eq__(self, other):
        return type(other) is Case and self.id == other.id


class DefinedCase(Case):

    def __init__(self,
                 id: int,
                 date_recorded: datetime,
                 incident_location: Point,
                 events: List[Event],
                 priority: float = None):
        super().__init__(id, date_recorded, incident_location, priority)
        self.events = events

    def iterator(self, ambulance, current_time):
        return iter(self.events)


# Implementation of a Case that stochastically generates random events while iterating
# Events are currently defined in this order:
# TO_INCIDENT -> AT_INCIDENT -> TO_HOSPITAL -> AT_HOSPITAL
class RandomCase(Case):

    def __init__(self,
                 id: int,
                 date_recorded: datetime,
                 incident_location: Point,
                 event_generator: EventGenerator,
                 priority: int = None):
        super().__init__(id, date_recorded, incident_location, priority)
        self.event_generator = event_generator

    def iterator(self, ambulance, current_time):
        hospital_location = None
        for event_type in [EventType.TO_INCIDENT, EventType.AT_INCIDENT, EventType.TO_HOSPITAL, EventType.AT_HOSPITAL,
                           EventType.TO_BASE]:

            event = self.event_generator.generate(ambulance=ambulance,
                                                  incident_location=self.incident_location,
                                                  timestamp=current_time,
                                                  event_type=event_type,
                                                  hospital_location=hospital_location)
            if event_type == EventType.TO_HOSPITAL:
                hospital_location = event.destination

            current_time = current_time + event.duration

            yield event
