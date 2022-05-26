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
        self._simulation_is_initialized = False

    @property
    def simulation_data(self):
        if self._env is not None:
            return self._env.simulation_data
        else:
            return None

    @simulation_data.setter
    def simulation_data(self, data):
        raise RuntimeError('Cannot override simulation_data dictionary.')

    def simulate(self, simulation_time, reset = False, trace = False, print_summary = True):
        ''' Ensure objects are initialized and run the simulation for
        specified duration.

        Arguments:
        simulation_time -- for how long to run the simulation measured
            in simulation time.
        reset -- if True then the simulation will be restarted from time
            zero. States of all devices and other assets will be reset
            to initial states. If False the simulation will continue
            from the current state for the specified duration.
        trace -- if True then events will be recorded and exported to
            a file. Otherwise the events will not be recorded or
            exported.
        print_summary -- if True a brief summary will be printed after
            the simulation.
        '''
        start = time.time()

        if not self._simulation_is_initialized or reset == True:
            self._env.reset()
            for obj in self._objects:
                obj.initialize(self._env)
            self._simulation_is_initialized = True

        produced_parts_before = self._get_part_count_in_sinks()
        self._env.run(simulation_time, trace = trace)
        produced_parts_after = self._get_part_count_in_sinks()

        stop = time.time()
        if print_summary:
            print(f'Simulation finished in {stop-start:.2f}s')
            print(f'Parts received by sink/s: {produced_parts_after - produced_parts_before}')

    def _get_part_count_in_sinks(self):
        from .factory_floor.sink import Sink  # Late import to avoid circular dependency.
        return sum(x.received_parts_count for x in self._objects if isinstance(x, Sink))

    def get_net_value_of_objects(self):
        ''' Calculates and returns the net value of objects provided
        when creating System.
        '''
        from .factory_floor.asset import Asset
        return sum(x.value for x in self._objects if isinstance(x, Asset))

