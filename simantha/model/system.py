import time

from ..utils import DataStorageType
from .simulation import Environment


class System:
    '''
    A `System` object contains configured manufacturing objects and is used to run the
    simulation.
    '''

    def __init__(self, objects = [], simulation_data_storage_type = DataStorageType.NONE):
        self.objects = objects
        self._simulation_data_storage_type = simulation_data_storage_type

    @property
    def simulation_data(self):
        return self._env.simulation_data

    @simulation_data.setter
    def simulation_data(self, data):
        raise RuntimeError('Cannot override simulation_data dictionary.')

    def simulate(self,
                 simulation_time = 0,
                 trace = False,
                 print_summary = True):
        start = time.time()

        self._env = Environment(trace = trace,
                                simulation_data_storage_type = self._simulation_data_storage_type)
        for obj in self.objects:
            obj.initialize(self._env)

        self._env.run(simulation_time)
        stop = time.time()

        if print_summary:
            print(f'Simulation finished in {stop-start:.2f}s')
            from .factory_floor.sink import Sink  # Late import to avoid circular dependency.
            producedParts = sum(
                x.received_parts_count for x in self.objects if isinstance(x, Sink))
            print(f'Parts produced: {producedParts}')

    def get_net_value(self):
        from .factory_floor.asset import Asset
        return sum(x.value for x in self.objects if isinstance(x, Asset))

