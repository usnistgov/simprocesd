import time

from . import Environment
from ..utils import DataStorageType


class System:
    ''' A System object is a convenient way to run the simulation and
    access simulation data.
    '''

    def __init__(self, objects = [], simulation_data_storage_type = DataStorageType.NONE):
        self._objects = objects
        self._env = Environment(simulation_data_storage_type = simulation_data_storage_type)

    @property
    def simulation_data(self):
        if self._env is not None:
            return self._env.simulation_data
        else:
            return None

    @simulation_data.setter
    def simulation_data(self, data):
        raise RuntimeError('Cannot override simulation_data dictionary.')

    def simulate(self, simulation_time = 0, trace = False, print_summary = True):
        ''' Initialize provided objects with the current Environment
        and run the simulation.

        Arguments:
        simulation_time -- simulation time when the simulation will
            stop. This argument is passed to Environment.run.
        trace -- if true then events will be recorded and exported to
            a file. This argument is passed to Environment.run.
        print_summary -- if true a brief summary will be printed after
            the simulation.
        '''
        start = time.time()

        for obj in self._objects:
            obj.initialize(self._env)

        self._env.run(simulation_time, trace = trace)
        stop = time.time()

        if print_summary:
            print(f'Simulation finished in {stop-start:.2f}s')
            from .factory_floor.sink import Sink  # Late import to avoid circular dependency.
            producedParts = sum(
                x.received_parts_count for x in self._objects if isinstance(x, Sink))
            print(f'Parts received by sink/s: {producedParts}')

    def get_net_value_of_objects(self):
        ''' Calculates and returns the net value of objects provided
        when creating System.
        '''
        from .factory_floor.asset import Asset
        return sum(x.value for x in self._objects if isinstance(x, Asset))

