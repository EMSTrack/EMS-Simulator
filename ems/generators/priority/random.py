# Generates a priority from a probabilistic distribution
from ems.generators.priority.priority import PriorityGenerator
from numpy.random import choice


class RandomPriorityGenerator(PriorityGenerator):

    def __init__(self, priorities=None, distribution=None):
        super().__init__(priorities=priorities)

        if priorities is None:
            priorities = [1, 2, 3, 4]

        if distribution is None:
            self.dist = [1 / len(priorities) for _ in priorities]
        else:
            self.dist = distribution

    def generate(self, timestamp=None):
        # Randomly choose
        return choice(self.priorities, 1, p=self.dist)[0]
