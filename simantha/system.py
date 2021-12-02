import copy
import multiprocessing
import random
import sys
import time
import warnings

# from .components.source import Source
# from .components.sink import Sink
# from .components.machine import Machine
# from .components.buffer import Buffer
from .maintainer import Maintainer
from .simulation import Environment


class System:
    """
    A ``System`` object contains configured manufacturing objects and is used to run the
    simulation.
    """

    def __init__(
        self,
        objects = [],
        maintainer = None
    ):
        self.objects = objects
        '''self.sources = []
        self.machines = []
        self.buffers = []
        self.sinks = []
        for obj in objects:
            if type(obj) == Source:
                self.sources.append(obj)
            elif isinstance(obj, Machine):
                self.machines.append(obj)
            elif type(obj) == Buffer:
                self.buffers.append(obj)
            elif type(obj) == Sink:
                self.sinks.append(obj)'''

        if maintainer is None:
            self.maintainer = Maintainer()
        else:
            self.maintainer = maintainer

        # Put machines at the front as they should be initialized first
        # self.objects.sort(key=lambda obj: not isinstance(obj, Machine))

    def initialize(self):
        for buffer in self.buffers:
            buffer.level = buffer.initial_level

        for sink in self.sinks:
            sink.level = sink.initial_level

        self.maintainer.utilization = 0

    def simulate(
        self,
        warm_up_time = 0,
        simulation_time = 0,
        verbose = True,
        trace = False,
        collect_data = True
    ):
        """
        The primary method for simulating a system.


        Parameters
        ----------
        warm_up_time : int
            The duration of the simulation warm up time. No data is collected during the
            warm up period.
        simulation_time : int
            The duration of the simulation.
        verbose : bool
            If ``True``, prints a summary upon completion of the simulation run.
        collect_data : bool
            If ``True``, objects in the system will collect their respective production
            and maintenance data. If ``False``, this data will not be stored which may
            be useful for very long simulations where memory becomes an issue.
        """
        start = time.time()
        # for machine in self.machines:
        #    machine.maintainer = self.maintainer

        self.env = Environment(trace = trace, collect_data = collect_data)
        for obj in self.objects:
            obj.initialize(self.env)

        self.maintainer.env = self.env
        # if self.maintainer.machines is None:
        #    self.maintainer.machines = self.machines
        self.maintainer.initialize()

        self.warm_up_time = warm_up_time
        self.simulation_time = simulation_time

        self.env.run(warm_up_time, simulation_time)

        # Clean up simulation data
        # for machine in self.machines:
        #    if machine.under_repair or machine.failed:
        #        machine.downtime += (self.env.now - machine.downtime_start)

        stop = time.time()
        if verbose:
            print(f'Simulation finished in {stop-start:.2f}s')
            from . import Sink  # Late import to avoid circular dependency.
            producedParts = sum(
                len(x.collected_parts) for x in self.objects if isinstance(x, Sink))
            print(f'Parts produced: {producedParts}')

    def iterate_simulation(
        self,
        replications,
        warm_up_time = 0,
        simulation_time = 0,
        store_system_state = False,
        verbose = True,
        jobs = 1,
        seedseed = 0
    ):
        """
        Conduct several simulation replications of the system with the option to do so 
        in parallel.


        Parameters
        ----------
        replications : int
            The number of simulation replications.
        warm_up_time : int
            The simulation warm up time for each replication.
        simulation_time : int
            The simulation duration for each replication.
        store_system_state : bool
            If ``True``, each replication will return a copy of the ``simantha.System``
            object at the end of its simulation run.
        verbose : bool
            If ``True``, prints a summary of the simulation replications.
        jobs : int
            The number of jobs to run in parallel.

        
        Returns
        -------
        list
            A list of tuples containing the results of each replication.

        """
        start = time.time()
        with multiprocessing.Pool(jobs) as p:
            args = [
                (seed, warm_up_time, simulation_time, store_system_state)
                for seed in range(seedseed, seedseed + replications)
            ]
            samples = p.starmap(self.simulate_in_parallel, args)
        stop = time.time()

        if verbose:
            print(f'Finished {replications} replications in {stop-start:.2f}s')

        return samples

'''
    def simulate_in_parallel(
        self, 
        seed, 
        warm_up_time, 
        simulation_time, 
        store_system_state=False
    ):
        try:
            random.seed()
            
            self.simulate(
                warm_up_time, 
                simulation_time, 
                verbose=False, 
                collect_data=store_system_state
            )

            availability = [
                (1 - machine.downtime/(warm_up_time+simulation_time)) 
                for machine in self.machines
            ]

            machine_production = [machine.parts_made for machine in self.machines]

            system_production = sum([sink.level for sink in self.sinks])

            if store_system_state:
                system_state = copy.deepcopy(self)
            else:
                system_state = None

            return (
                system_production, 
                machine_production, 
                availability, 
                system_state
            )
        
        except:
            return sys.exc_info()[0]
'''
