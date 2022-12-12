import time

from . import Environment
from ..utils import DataStorageType


class System:
    '''A required class that helps setup and run simulations.

    System handles Asset initialization and manages the Environment
    object to provide an easy to use interface for running simulations.

    Creating a new System sets it as the active System replacing another
    active System if there is one. Only the active system can run
    simulations.

    System object needs to be created before any Asset because Assets
    will automatically try to register themselves with the active
    System.

    Arguments
    ---------
    simulation_data_storage_type: DataStorageType, default=DataStorageType.MEMORY
        How to store <simulation_data>. Does not currently support
        DataStorageType.FILE
    '''

    _instance = None  # Last initialized System.

    @staticmethod
    def add_asset(new_asset):
        '''Register an Asset with the active System.

        Automatically called by newly created Assets.

        Note: System will keep a reference to this Asset so transitory
        assets should not be added here or they will remain loaded into
        memory. For example, Parts are not added here and parts are
        initialized by the Source that created them.

        Arguments
        ---------
        new_asset: Asset
            Asset to be registered.

        Raises
        ------
        RuntimeError
            System object must be created before non-transitory Assets.
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
        '''Stored datapoints added with
        environment.add_datapoint(list_label, sub_label, datapoint)

        | To retrieving a list of datapoints call:
        | system.simulation_data[list_label][sub_label]
        '''
        if self._env is not None:
            return self._env.simulation_data
        else:
            return None

    def simulate(self, simulation_duration, reset = True, trace = False, print_summary = True):
        '''Run the simulation for the specified duration.

        Ensures objects are initialized or re-initialized as needed.

        Arguments
        ---------
        simulation_duration: float
            For how long to run the simulation. Measured in simulation
            time.
        reset: bool, default=True
            If True then the simulation will be restarted from time
            zero and states of all Devices and other Assets will be
            reset to initial states. If False then the simulation will
            continue from the current simulation time.
        trace: bool, default=False
            If True then the executed events will be recorded and the
            trace will be exported to a file at
            '~/Downloads/environment_trace.json'
        print_summary: bool, default=True
            If True a brief summary will be printed at the end of the
            simulation.
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
        '''Calculate the net value of all Assets which are registered
        with the System.

        Returns
        -------
        float
            Net value of Assets.
        '''
        from .factory_floor.asset import Asset
        return sum(x.value for x in self._assets if isinstance(x, Asset))

    def find_assets(self, name = None, id_ = None, type_ = None, subtype = None):
        '''Search through Assets registered with the System.

        If multiple arguments are provided then it will return only the
        Assets that match all of the arguments.

        Arguments
        ---------
        name: str, optional
            Filter Assets by name.
        id_: int, optional
            Filter Assets by ID.
        type_: type, optional
            Filter Assets by class type, checks immediate class only.
        subtype: type, optional
            Filter Assets by class type, checks all of the Asset's types
            using isinstance()

        Returns
        -------
        list
            A list of Assets that match the provided arguments.
        '''
        rtn = []
        for a in self._assets:
            if (name == None or name == a.name) and \
                    (id_ == None or id_ == a.id) and \
                    (type_ == None or type(a) is type_) and \
                    (subtype == None or isinstance(a, subtype)):
                rtn.append(a)

        return rtn

