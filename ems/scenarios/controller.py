# Manages the progression of scenarios
from datetime import datetime, timedelta
from typing import List

from ems.scenarios.scenario import Scenario
from ems.triggers.trigger import Trigger

import numpy as np


class TriggerTuple:

    def __init__(self,
                 scenario: Scenario,
                 trigger: Trigger):
        self.scenario = scenario
        self.trigger = trigger

    def __eq__(self, other):
        return self.scenario == other.scenario and self.trigger == other.trigger

    def __str__(self):
        return "Scenario {}; Trigger {}".format(self.scenario.label, self.trigger.id)


# Current solution relies on keeping track of all scenario triggers that are active at a given time. Upon call to
# retrieve the next scenario, all active scenarios that have ended should end and all inactive scenarios that have
# started should start. Then the new scenario should be the scenario with the highest priority of the active
# triggers.

# However, the problem is made complex because the caller may not be progressing in a constant tick by tick manner
# but rather, by event based, variable interval time jumps. Inactive scenarios may cause a "rewind" in time back to
# the start of its time. Thus the algorithm is as follows:

#
class ScenarioController:

    def __init__(self,
                 scenarios: List[Scenario]):
        # Maintain a list of sorted triggers and their scenario
        tts = [TriggerTuple(scenario=s, trigger=t) for s in scenarios for t in s.triggers]
        self.inactive_tts = sorted(tts, key=lambda x: x.trigger.start_time)
        self.active_tts = []
        self.current_time = None

    def retrieve_initial_scenario(self, time):
        self.current_time = time
        ind = 0
        for tt in self.inactive_tts:
            if tt.trigger.start_time <= self.current_time:
                self.active_tts.append(tt)
                ind += 1
            else:
                break
        self.inactive_tts = self.inactive_tts[ind:]

        # Re-sort tts
        self.active_tts = sorted(self.active_tts, key=lambda x: -x.scenario.priority)
        self.inactive_tts = sorted(self.inactive_tts, key=lambda x: x.trigger.start_time)

        return self.active_tts[0].scenario, self.current_time

    # Returns the next scenario and the new time
    def retrieve_next_scenario(self, time: datetime):
        # Two lists:
        # Active_tts are all currently active tts in order of priority
        # Inactive_tts are all inactive tts in order of their start time
        current_tt = self.active_tts[0]
        if not current_tt.trigger.is_active(time):
            self.current_time = current_tt.trigger.finish_time + timedelta(seconds=1)
        else:
            self.current_time = time

        # Introduce any new scenarios 1 by 1 to check for one with higher priority. If none is found, then proceed
        # with the current scenario and current time (change scenario if current has ended)
        new_tt = None
        ind = 0
        for tt in self.inactive_tts:
            if tt.trigger.start_time <= self.current_time:
                self.active_tts.append(tt)
                ind += 1
                if tt.scenario.priority < current_tt.scenario.priority:
                    new_tt = tt
                    break
            else:
                break
        self.inactive_tts = self.inactive_tts[ind:]

        if new_tt is not None:
            self.current_time = new_tt.trigger.start_time

        # Retiring triggers
        new_actives = []
        for active_tt in self.active_tts:
            if active_tt.trigger.is_active(self.current_time):
                new_actives.append(active_tt)
            else:
                self.retire(active_tt)
        self.active_tts = new_actives

        # Re-sort tts
        self.active_tts = sorted(self.active_tts, key=lambda x: x.scenario.priority)
        self.inactive_tts = sorted(self.inactive_tts, key=lambda x: x.trigger.start_time)

        return self.active_tts[0].scenario, self.current_time

    def retire(self, tt):
        if tt.trigger.interval is not None:
            tt.trigger.update()
            self.inactive_tts.append(tt)
