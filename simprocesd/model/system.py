import concurrent.futures
import time

from . import Environment, ResourceManager


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
    resource_manager: ResourceManager, default=None
        A ResourceManager instance to use for this simulation. If None
        then the default ResourceManager will be used.
    '''

    _instance = None  # Last initialized System.

    @staticmethod
    def add_asset(new_asset):
        '''Register an Asset with the active System.

        Automatically called by newly created Assets. If the simulation
        is already in progress then the new_asset will be initialized
        immediately.

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
            if System._instance._simulation_is_initialized:
                new_asset.initialize(System._instance._env)

    def __init__(self, resource_manager = None):
        self._assets = []
        if resource_manager == None:
            resource_manager = ResourceManager()
        self._env = Environment(resource_manager = resource_manager)
        self._simulation_is_initialized = False

        System._instance = self

    @property
    def env(self):
        '''Simulation's Environment instance.
        '''
        return self._env

    @property
    def simulation_data(self):
        '''Stored datapoints added with
        Environment.add_datapoint(list_label, sub_label, datapoint)

        | To retrieving a list of datapoints call:
        | system.simulation_data[list_label][sub_label]
        '''
        return self._env.simulation_data

    @property
    def resource_manager(self):
        '''ResourceManager instance.
        '''
        return self._env.resource_manager

    def simulate(self, simulation_duration, trace = False, print_summary = True):
        '''Run the simulation for the specified duration.

        Ensures Assets are initialized when called for the first time.

        Arguments
        ---------
        simulation_duration: float
            For how long to run the simulation. Measured in simulation
            time.
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

        if not self._simulation_is_initialized:
            self.resource_manager.initialize(self._env)
            self._initialize_assets()
            self._simulation_is_initialized = True

        produced_parts_before = self._get_part_count_in_sinks()
        self._env.run(simulation_duration, trace = trace)
        produced_parts_after = self._get_part_count_in_sinks()

        stop = time.time()
        if print_summary:
            print(f'Simulation finished in {stop-start:.2f}s')
            print(f'Parts received by sink(s): {produced_parts_after - produced_parts_before}')

    def _initialize_assets(self):
        for asset in self._assets:
            asset.initialize(self._env)

    def _get_part_count_in_sinks(self):
        from .factory_floor.sink import Sink  # Late import to avoid circular dependency.
        return sum(sink.received_parts_count for sink in self.find_assets(type_ = Sink))

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

    @staticmethod
    def simulate_multiple_times(simulation, number_of_simulations, max_processes = 0,
                                *args, **kwargs):
        '''Run a simulation multiple times using multiple processes.

        Simulation function is executed multiple times with a new
        System instance each time. The simulation function needs to
        initialize the model and run the simulation by calling
        system_parameter.simulate(...)

        Note
        ----
        It is recommended to familiarize yourself with Python's
        multi-process code execution such as each process having a
        separate copy of static variables.
        Each process may run multiple simulations, one after another.

        Arguments
        ---------
        simulation: function
            Function that sets up the model and runs it. The function
            will be called with 2+ parameter:
            - System instance to be used for this simulation.
            - integer index of the simulation
            - additional arguments, see *args, **kwargs
        number_of_simulations: int > 0
            Number of times to run <simulation>.
        max_processes: int, default=0
            Maximum number of processes to create for running
            simultaneous simulations.
            If 0, then simulations will run one after another in the
            current thread (and the current process).
            If None, then default to the number of processors on the
            machine
        *args, **kwargs:
            Additional arguments will be passed to the simulation
            function.

        Returns
        -------
        list
            A list of System objects that were used to run each
            simulation. List length will equal <iterations>.

        Raises
        ------
        AttributeError
            If you see error like:
            Can't pickle local object 'simulation.<locals>.function'
            It means you defined an anonymous function (e.g. function
            within a function) in your code that the multiprocess
            setup does not support.
        '''
        assert number_of_simulations > 0
        assert max_processes == None or max_processes >= 0

        # Run simulations on current thread
        if max_processes == 0:
            return [System._simulation_helper(simulation, i, *args, **kwargs) for i in range(number_of_simulations)]

        with concurrent.futures.ProcessPoolExecutor(max_processes) as thread_pool:
            futures = []
            for i in range(number_of_simulations):
                futures.append(thread_pool.submit(System._simulation_helper,
                                                  simulation, i, *args, **kwargs))

            systems = []
            for i in range(number_of_simulations):
                systems.append(futures[i].result(timeout = None))

        return systems

    @staticmethod
    def _simulation_helper(simulation, index, *args, **kwargs):
        new_system = System()
        simulation(new_system, index, *args, **kwargs)
        return new_system

