''' Expected parts produced: 1439
Average quality: ~80%
Average weight: ~18
'''
import random

from simprocesd.model import System
from simprocesd.model.factory_floor import Part, Source, Machine, Sink


class CustomPart(Part):

    def __init__(self, name = None, quality = 1.0, weight = 0):
        super().__init__(name, 0, quality)
        # Assign weight and save starting value.
        self.weight = self._initial_weight = weight

    def initialize(self, env):
        # Updating initialize is not strictly necessary for this
        # example because of the limited usage of CustomPart.
        super().initialize(env)
        # Reset weight to starting value.
        self.weight = self._initial_weight

    def make_copy(self):
        self.copy_counter += 1
        return CustomPart(f'{self.name}_{self.copy_counter}', self.quality, self.weight)


def process_part(part, min_, max_):
    diff = max_ - min_
    # Quality is increased.
    part.quality += max_ - diff * random.random()
    # Weight is decreased.
    part.weight *= 0.75 + 0.2 * random.random()


def main():
    system = System()

    source = Source(sample_part = CustomPart('part', 0, 25))
    M1 = Machine('M1',
                 upstream = [source],
                 cycle_time = 1)
    M1.add_finish_processing_callback(lambda m, p: process_part(p, 0.5, 0.75))
    M2 = Machine('M2',
                 upstream = [M1],
                 cycle_time = 1)
    M2.add_finish_processing_callback(lambda m, p: process_part(p, 0.1, 0.25))
    sink = Sink(upstream = [M2], collect_parts = True)

    # If time units are minutes then simulation period is a day.
    system.simulate(simulation_duration = 24 * 60)

    average_quality = (
        sum([part.quality for part in sink.collected_parts]) / len(sink.collected_parts)
    )
    average_weight = (
        sum([part.weight for part in sink.collected_parts]) / len(sink.collected_parts)
    )
    print(f'Average part quality: {average_quality:.2%}')
    print(f'Average part weight: {average_weight:.4g}')


if __name__ == '__main__':
    main()
