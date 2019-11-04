from ems.datasets.location import LocationSet


class AmbulanceBaseSelector:

    # TODO -- More info
    def select(self, num_ambulances):
        raise NotImplementedError()


class RoundRobinBaseSelector(AmbulanceBaseSelector):
    """ Assigned ambulances to bases in round robin order.  """

    def __init__(self,
                 base_set: LocationSet):
        self.base_set = base_set

    def select(self, num_ambulances):
        bases = []

        for index in range(num_ambulances):
            base_index = index % len(self.base_set)
            bases.append(self.base_set.locations[base_index])

        return bases


class TijuanaBaseSelector(AmbulanceBaseSelector):
    """ Based on the original Dibene paper. """

    def __init__(self,
                 base_set: LocationSet):
        self.base_set = base_set

    def select(self, num_ambulances):
        """ This returns list of bases that each ambulance will reside at.  """
        no_ambulances = [-6]
        one_ambulances = [i for i in range(-8, 0) if i not in no_ambulances]
        two_ambulances = [-8, -7, -4, -1]

        ambulances = one_ambulances + two_ambulances

        bases = []

        for base_index in ambulances:
            bases.append(self.base_set.locations[base_index])

        if len(bases) != num_ambulances:
            raise Exception("Wrong number of bases were being assigned to ambulances.")

        return bases
