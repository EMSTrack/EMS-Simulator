import random

import pandas as pd
from geopy import Point

from ems.algorithms.base import AmbulanceBaseSelector
from ems.datasets.location import LocationSet
from ems.generators.location import LocationGenerator
from ems.models.ambulance import Ambulance
from ems.models.capability import Capability
from ems.utils import parse_headered_csv


class AmbulanceSet:

    def __init__(self,
                 ambulances=None,
                 filename=None,
                 headers=None):

        self.headers = headers

        if headers is None:
            self.headers = ["id", "base_latitude", "base_longitude", "capability"]

        if filename is not None:
            ambulances = self.read(filename)

        self.filename = filename
        self.ambulances = ambulances

    def __len__(self):
        return len(self.ambulances)

    def write_to_file(self, output_filename):
        a = [{"id": ambulance.id,
              "base_latitude": ambulance.base.latitude,
              "base_longitude": ambulance.base.longitude,
              "capability": ambulance.capability.name} for ambulance in self.ambulances]
        df = pd.DataFrame(a, columns=self.headers)
        df.to_csv(output_filename, index=False)

    def read(self, filename):

        # Read ambulance from a headered CSV into a pandas dataframe
        ambulances_df = parse_headered_csv(filename, self.headers)

        # TODO -- generalize
        id_key = self.headers[0]
        b_latitude_key = self.headers[1]
        b_longitude_key = self.headers[2]
        capability_key = self.headers[3]

        # Generate list of models from dataframe
        a = []
        for index, row in ambulances_df.iterrows():
            base = Point(row[b_latitude_key],
                         row[b_longitude_key])
            ambulance = Ambulance(id=row[id_key],
                                  base=base,
                                  capability=Capability[row[capability_key]])
            a.append(ambulance)

        return a


class BaseSelectedAmbulanceSet(AmbulanceSet):

    def __init__(self,
                 count: int,
                 base_selector: AmbulanceBaseSelector):
        self.count = count
        self.base_selector = base_selector
        super().__init__(self.initialize_ambulances())

    def initialize_ambulances(self):
        bases = self.base_selector.select(self.count)
        ambulances = [Ambulance(id=str(i),
                                base=bases[i],
                                location=bases[i]) for i in range(self.count)]

        return ambulances

    def __len__(self):
        return self.count


class CustomAmbulanceSet(AmbulanceSet):

    def __init__(self,
                 bases: LocationSet):
        self.bases = bases
        super().__init__(ambulances=self.initialize_ambulances())

    def initialize_ambulances(self):
        ambulances = [Ambulance(id=str(i),
                                base=self.bases[i],
                                location=self.bases[i]) for i in range(len(self.bases))]
        return ambulances

    def __len__(self):
        return len(self.bases)


class RandomAmbulanceSet(AmbulanceSet):

    def __init__(self,
                 count: int,
                 base_generator: LocationGenerator):
        self.count = count
        self.base_generator = base_generator
        super().__init__(self.initialize_ambulances())

    def initialize_ambulances(self):
        ambulances = []
        for index in range(self.count):
            base = self.base_generator.generate(None)
            capability = random.choice(list(Capability))
            ambulances.append(Ambulance(id=str(index),
                                        base=base,
                                        capability=capability,
                                        deployed=False,
                                        location=base))

        return ambulances
