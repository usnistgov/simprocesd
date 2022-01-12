import time

from .simulation import Environment


class System:
    '''
    A `System` object contains configured manufacturing objects and is used to run the
    simulation.
    '''

    def __init__(self, objects = []):
        self.objects = objects

    def simulate(self,
                 simulation_time = 0,
                 trace = False,
                 collect_data = True):
        start = time.time()

        self._env = Environment(trace = trace, collect_data = collect_data)
        for obj in self.objects:
            obj.initialize(self._env)

        self._env.run(simulation_time)
        stop = time.time()

        print(f'Simulation finished in {stop-start:.2f}s')
        from .factory_floor.sink import Sink  # Late import to avoid circular dependency.
        producedParts = sum(
            x.received_parts_count for x in self.objects if isinstance(x, Sink))
        print(f'Parts produced: {producedParts}')

    def get_net_value(self):
        from .factory_floor.asset import Asset
        return sum(x.value for x in self.objects if isinstance(x, Asset))

