from datetime import datetime
from typing import List

from geopy import Point

from ems.generators.duration import DurationGenerator
from ems.generators.event import EventGenerator
from ems.generators.location import LocationGenerator
from ems.generators.priority import PriorityGenerator, RandomPriorityGenerator
from ems.models.case import RandomCase, Case
from ems.scenarios.controller import ScenarioController
from ems.scenarios.scenario import Scenario
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


class ScenarioCaseSet(CaseSet):

    def __init__(self,
                 time: datetime,
                 scenarios: List[Scenario],
                 quantity: int = None):
        super().__init__(time)
        self.current_scenario = None
        self.scenario_controller = ScenarioController(scenarios=scenarios)
        self.scenarios = scenarios
        self.scenario_iterators = {scenario.label: scenario.case_set.iterator() for scenario in scenarios}
        self.current_scenario = None
        self.time = time
        self.quantity = quantity

    def __len__(self):
        return self.quantity

    def iterator(self):

        k = 1

        self.current_scenario, self.time = self.scenario_controller.retrieve_next_scenario(self.time)

        while k <= self.quantity:

            # We want to
            # 1. Generate case with current scenario
            # 2. Trigger scenarios with the time of the new case
            # 3. If a new scenario happens, generate a new case with that new scenario
            #    Otherwise, keep the generated case
            # Loop

            # Step 1: Determine scenario
            new_scenario = True
            new_case = None

            while new_scenario:

                # print("Temp Time: {}".format(self.time))
                # print("Temp Current scenario: {}".format(self.current_scenario.label))

                # Step 1: Generate case with the current scenario's iterator
                new_case = next(self.scenario_iterators[self.current_scenario.label])

                # print("Temp next case time: {}".format(new_case.date_recorded))

                self.scenario_controller.flush_inactive()

                # Step 2
                next_scenario, next_time = self.scenario_controller.retrieve_next_scenario(new_case.date_recorded)

                # Step 3
                if next_scenario == self.current_scenario:
                    self.time = new_case.date_recorded
                    new_scenario = False

                else:
                    self.current_scenario = next_scenario
                    self.time = next_time

                # Update times in all case sets
                for s in self.scenarios:
                    s.case_set.set_time(self.time)

                self.scenario_controller.flush_inactive()

            # self.scenario_controller.set_times(time=self.time)

            # TODO These could be useful as logs
            # print("Next Scenario: {}".format(self.current_scenario.label))
            # print("Next case time: {}".format(new_case.date_recorded))

            new_case.id = k
            k += 1

            yield new_case
