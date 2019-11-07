from datetime import datetime, timedelta


class Trigger:

    def is_active(self, time: datetime, **kwargs):
        raise NotImplementedError()

    def update(self):
        raise NotImplementedError()


# TODO -- Code does not support defining a time trigger with a start time before the start of the sim with some interval
class TimeTrigger(Trigger):

    def __init__(self, start_time: datetime,
                 duration: int,
                 interval: int = None):
        self.start_time = start_time
        self.duration = timedelta(hours=duration)
        self.interval = timedelta(hours=interval) if interval else None
        self.finish_time = start_time + self.duration

    def is_active(self,
                  time: datetime,
                  **kwargs):

        # Time from start
        diff = time - self.start_time

        # Time is before trigger start time
        if diff < timedelta(seconds=0) or diff > self.duration:
            return False

        # In range
        return True

    def update(self):
        if self.interval is not None:
            self.start_time += self.interval
            self.finish_time += self.interval
