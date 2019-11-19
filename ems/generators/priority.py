import numpy


class PriorityGenerator:
    """
    Selects a priority from the list of provided priorities
    """

    def __init__(self, priorities):
        """
        :param priorities: List of provided priorities
        :type priorities: List<Priority>
        """
        self.priorities = priorities

    # TODO -- kwargs through generate to allow for generation based on other params
    def generate(self, timestamp=None):
        """
        :param timestamp: The timestamp of when to generate the priority. Can be none. Main purpose is to allow for varying priority selected by time of day
        :type timestamp: datetime
        :return: The selected priority
        :rtype: Priority
        """
        raise NotImplementedError()


class RandomPriorityGenerator(PriorityGenerator):
    """
    Selects a priority according to a provided distribution from the list of provided priorities
    """

    def __init__(self, priorities=None, distribution=None):
        """
        All elements in distribution must sum to 0. Priorities will be initialized to 1,2,3,4 if none is provided.
        Distribution is uniform if not specified.

        :param priorities: The priorities to select from
        :type priorities: List<Priority>
        :param distribution: The provided distribution of priorities
        :type distribution: List<float>
        """
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
        return numpy.random.choice(self.priorities, 1, p=self.dist)[0]
