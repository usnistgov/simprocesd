import time

from . import Environment
from ..utils import DataStorageType


class System:
    ''' A System object is a convenient way to run the simulation and
    access simulation data.
    System needs to be created before other devices and assets because
    those objects will automatically register themselves with the last
    instantiated System object.
    When a new System object is created the previous System instance can
    no longer run simulations but the data in it can still be accessed.
    '''

    _instance = None  # Last initialized System.

    @staticmethod
    def add_asset(new_asset):
        ''' Automatically called by newly initialized Assets.
        Adds new_asset to the last created System so the Asset can be
        initialized and simulated by the System.

        Note: System will keep a reference to this asset so transitory
        assets should not be added here. For example Part is not added
        here but is instead initialized by Source which created it.
        '''
        if System._instance == None:
            raise RuntimeError('A System object must be initialized before creating any asset.')
        if new_asset not in System._instance._assets:
            System._instance._assets.append(new_asset)

    def __init__(self, simulation_data_storage_type = DataStorageType.MEMORY):
        self._assets = []
        self._env = Environment(simulation_data_storage_type = simulation_data_storage_type)
        self._simulation_is_initialized = False

        System._instance = self

    @property
    def simulation_data(self):
        if self._env is not None:
            return self._env.simulation_data
        else:
            return None

    def simulate(self, simulation_duration, reset = False, trace = False, print_summary = True):
        ''' Ensure objects are initialized and run the simulation for
        specified duration.

        Arguments:
        simulation_duration -- for how long to run the simulation
            measured in simulation time.
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
        if System._instance != self:
            raise RuntimeError('This System can no longer simulate because a new one was created.')
        start = time.time()

        if not self._simulation_is_initialized or reset == True:
            self._env.reset()
            for asset in self._assets:
                asset.initialize(self._env)
            self._simulation_is_initialized = True

        produced_parts_before = self._get_part_count_in_sinks()
        self._env.run(simulation_duration, trace = trace)
        produced_parts_after = self._get_part_count_in_sinks()

        stop = time.time()
        if print_summary:
            print(f'Simulation finished in {stop-start:.2f}s')
            print(f'Parts received by sink/s: {produced_parts_after - produced_parts_before}')

    def _get_part_count_in_sinks(self):
        from .factory_floor.sink import Sink  # Late import to avoid circular dependency.
        return sum(x.received_parts_count for x in self._assets if isinstance(x, Sink))

    def get_net_value_of_assets(self):
        ''' Calculates and returns the net value of objects provided
        when creating System.
        '''
        from .factory_floor.asset import Asset
        return sum(x.value for x in self._assets if isinstance(x, Asset))

