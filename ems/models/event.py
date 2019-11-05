from datetime import timedelta
from enum import Enum

from geopy import Point


class EventType(Enum):
    __order__ = 'TO_INCIDENT AT_INCIDENT TO_HOSPITAL AT_HOSPITAL TO_BASE OTHER'

    TO_INCIDENT = "Heading to Incident"
    AT_INCIDENT = "Attending to Incident"
    TO_HOSPITAL = "Heading to Hospital"
    AT_HOSPITAL = "Dropping off Patient at Hospital"
    TO_BASE = "Returning to Base"
    OTHER = "Other"


class Event:

    def __init__(self,
                 destination: Point,
                 event_type: EventType,
                 duration: timedelta = None,
                 error=None,
                 sim_dest=None):
        self.destination = destination
        self.event_type = event_type
        self.duration = duration
        self.error = error
        self.sim_dest = sim_dest
