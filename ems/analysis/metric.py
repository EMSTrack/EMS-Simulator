from datetime import datetime
from datetime import timedelta
from typing import List

import pandas as pd


class Metric:

    def __init__(self, tag: str):
        self.tag = tag

    def __eq__(self, other):
        return self.tag == other.tag

    def calculate(self,
                  timestamp: datetime,
                  **kwargs):
        raise NotImplementedError()


class CountPending(Metric):

    def __init__(self, tag="count_pending"):
        super().__init__(tag)

    def calculate(self, timestamp: datetime, **kwargs):
        if "pending_cases" not in kwargs:
            return None

        pending_cases = kwargs["pending_cases"]
        return len(pending_cases)


class TotalDelay(Metric):

    def __init__(self, tag="total_delay"):
        super().__init__(tag)

    def calculate(self, timestamp: datetime, **kwargs):

        if "pending_cases" not in kwargs:
            return None

        pending_cases = kwargs["pending_cases"]
        total_delay = timedelta(seconds=0)

        for case in pending_cases:
            total_delay += timestamp - case.date_recorded

        return total_delay


class MetricAggregator:
    def __init__(self,
                 metrics: List[Metric] = None):

        if metrics is None:
            metrics = []

        tags = []
        for metric in metrics:
            # Allow for a tag to be a list of tags.
            if isinstance(metric.tag, list):
                for each_tag in metric.tag:
                    if each_tag in tags:
                        raise Exception("Metric with tag '{}' already exists".format(each_tag))
                    tags.append(each_tag)
            else:
                if metric.tag in tags:
                    raise Exception("Metric with tag '{}' already exists".format(metric.tag))
                tags.append(metric.tag)

        self.tags = tags  # The flattened list of tag strings.
        self.metrics = metrics
        self.results = []

    def add_metric(self, metric: Metric):

        if metric in self.metrics:
            raise Exception("Metric with tag '{}' already exists".format(metric.tag))

        self.metrics.append(metric)

    def remove_metric(self, metric: Metric):
        self.metrics.remove(metric)

    def calculate(self,
                  timestamp: datetime,
                  **kwargs):
        d = {"timestamp": timestamp}
        for metric in self.metrics:
            calculation = metric.calculate(timestamp, **kwargs)
            # If a calculation is returned, at least one metric exists.
            if calculation is not None:
                if isinstance(metric.tag, list):
                    for i in range(len(metric.tag)):
                        d[metric.tag[i]] = calculation[i]
                else:
                    d[metric.tag] = calculation

        self.results.append(d)
        return d

    def write_to_file(self, output_filename):
        df = pd.DataFrame(self.results, columns=["timestamp"] + self.tags)
        df.to_csv(output_filename, index=False)
