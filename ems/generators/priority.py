from numpy.random import choice


# Interface for a priority generator
class PriorityGenerator:

    def __init__(self, priorities):
        self.priorities = priorities

    def generate(self, timestamp=None):
        raise NotImplementedError()


# Generates a priority from a probabilistic distribution
class RandomPriorityGenerator(PriorityGenerator):

    def __init__(self, priorities=None, distribution=None):
        super().__init__(priorities=priorities)

        if priorities is None:
            priorities = [1, 2, 3, 4]
        self.priorities = priorities

        if distribution is None:
            self.dist = [1 / len(priorities) for _ in priorities]
        else:
            self.dist = distribution

        # Validate function args
        if sum(self.dist) != 1.0:
            raise Exception("Sum of dist should add up to 100%")
        if len(self.dist) != len(priorities):
            raise Exception("Provided dist and priorities are not equal in length")

    def generate(self, timestamp=None):
        # Randomly choose
        return choice(self.priorities, 1, p=self.dist)[0]
