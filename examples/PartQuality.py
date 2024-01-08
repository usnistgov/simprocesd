''' Expected parts produced: 1438
M1 average quality: ~95%
M2 average quality: ~67%
M3 average quality: ~43%
'''
import random

from simprocesd.model import System
from simprocesd.model.factory_floor import PartGenerator, Source, PartProcessor, Buffer, Sink
from simprocesd.utils.simulation_info_utils import print_produced_parts_and_average_quality


def update_quality(part, min_, max_):
    diff = max_ - min_
    part.quality *= max_ - diff * random.random()


def main():
    system = System()

    source = Source(part_generator = PartGenerator('Part', value = 0, quality = 1))
    M1 = PartProcessor('M1',
                       upstream = [source],
                       cycle_time = 1)
    M1.add_finish_processing_callback(lambda m, p: update_quality(p, 0.9, 1))
    B1 = Buffer('B1', upstream = [M1], capacity = 10)
    M2 = PartProcessor('M2',
                       upstream = [B1],
                       cycle_time = 2)
    M2.add_finish_processing_callback(lambda m, p: update_quality(p, 0.6, 0.8))
    M3 = PartProcessor('M3',
                       upstream = [B1],
                       cycle_time = 2)
    M3.add_finish_processing_callback(lambda m, p: update_quality(p, 0.3, 0.6))
    sink = Sink(upstream = [M2, M3], collect_parts = True)

    random.seed(1)
    # If time units are minutes then simulation period is a day.
    system.simulate(simulation_duration = 24 * 60)

    print_produced_parts_and_average_quality(system, [M1, M2, M3])


if __name__ == '__main__':
    main()
