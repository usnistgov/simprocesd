import time

from .simulation import Environment


class System:
    '''
    A `System` object contains configured manufacturing objects and is used to run the
    simulation.
    '''

    def __init__(self, objects = [], maintainer = None):
        self.objects = objects
        self._maintainer = maintainer

    def simulate(self,
                 simulation_time = 0,
                 verbose = True,
                 trace = False,
                 collect_data = True):
        start = time.time()

        self._env = Environment(trace = trace, collect_data = collect_data)
        for obj in self.objects:
            obj.initialize(self._env)

        if self.maintainer != None:
            self.maintainer.initialize(self._env)

        self.simulation_time = simulation_time

        self._env.run(simulation_time)

        stop = time.time()
        if verbose:
            print(f'Simulation finished in {stop-start:.2f}s')
            from . import Sink  # Late import to avoid circular dependency.
            producedParts = sum(
                x.received_parts_count for x in self.objects if isinstance(x, Sink))
            print(f'Parts produced: {producedParts}')
