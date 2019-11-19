import bisect
from datetime import datetime
from datetime import timedelta
from typing import List

import pandas as pd

from ems.models.ambulance import Ambulance
from ems.models.case import Case
from ems.models.event import Event, EventType


class CaseRecord:
    """
    Representation of a finished case and all its details
    """

    def __init__(self,
                 case: Case,
                 ambulance: Ambulance,
                 start_time: datetime,
                 event_history: List[Event]):
        """
        :param case: The case
        :type case: Case
        :param ambulance: The ambulance assigned to the case
        :type ambulance: Ambulance
        :param start_time: The time an ambulance was dispatched to the case
        :type start_time: datetime
        :param event_history: The events associated with the case
        :type event_history: List<Event>
        """
        self.case = case
        self.ambulance = ambulance
        self.event_history = event_history
        self.start_time = start_time

    def __lt__(self, other):
        return self.case < other.case


class CaseRecordSet:
    """
    Represents a set of case records
    """

    def __init__(self,
                 case_records: List[CaseRecord] = None):
        """
        :param case_records: List of case records
        :type case_records: List<CaseRecord>
        """
        if case_records is None:
            case_records = []

        self.case_records = case_records
        self.case_records.sort()

    def add_case_record(self, case_record: CaseRecord):
        """
        Adds a case record to the set

        :param case_record: Case record to add
        :type case_record: CaseRecord
        """
        bisect.insort(self.case_records, case_record)

    def write_to_file(self, output_filename):
        """
        Writes the case records to a CSV file with the given params for each case:
            - Case ID
            - Date recorded
            - Emergency latitude
            - Emergency longitude
            - Case priority
            - Assigned ambulance ID
            - Time the case was started
            - For each event:
                - Location latitude
                - Location longitude
                - Duration

        :param output_filename: Output filename
        :type output_filename: string
        """
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
