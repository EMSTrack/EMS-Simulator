from ems.datasets.location import LocationSet


# TODO -- There is a better solution for mapping ambulances to bases, for example, manually by index
class AmbulanceBaseSelector:
    """
    Defines a strategy for mapping ambulances to bases
    """

    def select(self,
               num_ambulances: int):
        """
        Based on the number of provided ambulances, returns a list of bases of size num_ambulances

        :param num_ambulances: The number of ambulances to map
        :type num_ambulances: int
        :return: The list of bases selected
        :rtype: List<Base>
        """
        raise NotImplementedError()


class RoundRobinBaseSelector(AmbulanceBaseSelector):
    """
    Assigns ambulances to bases in round robin order
    """

    def __init__(self,
                 base_set: LocationSet):
        """
        :param base_set: Set of bases to select from
        :type base_set: BaseSet
        """
        self.base_set = base_set

    def select(self, num_ambulances):
        bases = []

        for index in range(num_ambulances):
            base_index = index % len(self.base_set)
            bases.append(self.base_set.locations[base_index])

        return bases
