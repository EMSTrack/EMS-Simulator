from datetime import datetime
from typing import List

from geopy import Point

from ems.generators.duration import DurationGenerator
from ems.generators.event import EventGenerator
from ems.generators.location import LocationGenerator
from ems.generators.priority import PriorityGenerator, RandomPriorityGenerator
from ems.models.case import RandomCase, Case
from ems.utils import parse_headered_csv


class CaseSet:

    def __init__(self, time):
        self.time = time

    def __len__(self):
        raise NotImplementedError()

    def iterator(self):
        raise NotImplementedError()

    def get_time(self):
        return self.time

    def set_time(self, time):
        self.time = time


class CSVCaseSet(CaseSet):

    def __init__(self,
                 filename: str,
                 event_generator: EventGenerator,
                 headers=None):

        if headers is None:
            headers = ["id", "date", "latitude", "longitude", "priority"]

        self.headers = headers
        self.filename = filename
        self.event_generator = event_generator
        self.cases = self.read_cases()
        super().__init__(self.cases[0].date_recorded)

    def iterator(self):
        return iter(self.cases)

    def __len__(self):
        return len(self.cases)

    def read_cases(self):

        # Read cases from CSV into a pandas dataframe
        cases_df = parse_headered_csv(self.filename, self.headers)

        # TODO -- Pass in dict or find another way to generalize ordering of headers
        id_key = self.headers[0]
        timestamp_key = self.headers[1]
        latitude_key = self.headers[2]
        longitude_key = self.headers[3]
        priority_key = self.headers[4] if len(self.headers) > 3 else None

        # Generate list of models from dataframe
        cases = []
        for index, row in cases_df.iterrows():
            case = RandomCase(id=row[id_key],
                              date_recorded=datetime.strptime(row[timestamp_key], '%Y-%m-%d %H:%M:%S.%f'),
                              incident_location=Point(row[latitude_key], row[longitude_key]),
                              event_generator=self.event_generator,
                              priority=row[priority_key] if priority_key is not None else None)
            cases.append(case)

        cases.sort(key=lambda x: x.date_recorded)

        return cases


# Implementation of a case set which is instantiated from a list of already known cases
class DefinedCaseSet(CaseSet):

    def __init__(self, cases: List[Case]):
        self.cases = cases
        super().__init__(self.cases[0].date_recorded)

    def __len__(self):
        return len(self.cases)

    def iterator(self):
        return iter(self.cases)


# Implementation of a case set that randomly generates cases while iterating
class RandomCaseSet(CaseSet):

    def __init__(self,
                 time: datetime,
                 case_time_generator: DurationGenerator,
                 case_location_generator: LocationGenerator,
                 event_generator: EventGenerator,
                 case_priority_generator: PriorityGenerator = RandomPriorityGenerator(),
                 quantity: int = None):
        super().__init__(time)
        self.time = time
        self.case_time_generator = case_time_generator
        self.location_generator = case_location_generator
        self.priority_generator = case_priority_generator
        self.event_generator = event_generator
        self.quantity = quantity

    def iterator(self):
        k = 1

        while self.quantity is None or k <= self.quantity:
            # Compute time and location of next event via generators
            duration = self.case_time_generator.generate(timestamp=self.time)["duration"]

            self.time = self.time + duration
            point = self.location_generator.generate(self.time)
            priority = self.priority_generator.generate(self.time)

            # Create case
            case = RandomCase(id=k,
                              date_recorded=self.time,
                              incident_location=point,
                              event_generator=self.event_generator,
                              priority=priority)

            k += 1

            yield case

    def __len__(self):
        return self.quantity
