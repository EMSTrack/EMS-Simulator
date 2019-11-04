import bisect
from datetime import datetime
from datetime import timedelta
from typing import List

import pandas as pd

from ems.models.ambulance import Ambulance
from ems.models.case import Case
from ems.models.event import Event, EventType


class CaseRecord:

    def __init__(self,
                 case: Case,
                 ambulance: Ambulance,
                 start_time: datetime,
                 event_history: List[Event]):
        self.case = case
        self.ambulance = ambulance
        self.event_history = event_history
        self.start_time = start_time

    def __lt__(self, other):
        return self.case < other.case


class CaseRecordSet:

    def __init__(self,
                 case_records: List[CaseRecord] = None):

        if case_records is None:
            case_records = []

        self.case_records = case_records
        self.case_records.sort()

    def add_case_record(self, case_record: CaseRecord):
        bisect.insort(self.case_records, case_record)

    def write_to_file(self, output_filename):
        a = []
        for case_record in self.case_records:

            d = {"id": case_record.case.id,
                 "date": case_record.case.date_recorded,
                 "latitude": case_record.case.incident_location.latitude,
                 "longitude": case_record.case.incident_location.longitude,
                 "priority": case_record.case.priority,
                 "ambulance": case_record.ambulance.id,
                 "start_time": case_record.start_time}

            total_durations_other = timedelta(minutes=0)
            for event in case_record.event_history:

                if event == EventType.OTHER:
                    total_durations_other += event.duration
                else:

                    d[event.event_type.name + "_duration"] = event.duration

                    if event.event_type == EventType.TO_HOSPITAL:
                        d["hospital_latitude"] = event.destination.latitude
                        d["hospital_longitude"] = event.destination.longitude

            d["OTHER_duration"] = total_durations_other

            a.append(d)

        event_labels = [event_type.name + "_duration" for event_type in EventType]

        df = pd.DataFrame(a, columns=["id", "date", "latitude", "longitude",
                                      "priority", "ambulance", "start_time"] + event_labels +
                                     ["hospital_latitude", "hospital_longitude"])
        df.to_csv(output_filename, index=False)
