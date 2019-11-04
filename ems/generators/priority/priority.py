# Interface for a priority generator
class PriorityGenerator:

    def __init__(self, priorities):
        self.priorities = priorities

    def generate(self, timestamp=None):
        raise NotImplementedError()
