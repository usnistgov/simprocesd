''' Expected parts received by sink: 999-1000
Processor should have received 1000 parts.
PartFixer should have received about 750 parts.
Processor average output part quality should be around 0.51
PartFixer average output part quality should be around 0.96
'''
import random

from ..model import System
from ..model.factory_floor import Source, Machine, Sink, Filter
from ..utils import DataStorageType, print_produced_parts_and_average_quality


def process_part(part):
    part.quality = random.random()


def improve_part(part):
    part.quality = min(1, part.quality + 0.75)


def main():
    source = Source()

    M1 = Machine('Processor', upstream = [source], cycle_time = 1)
    M1.add_finish_processing_callback(process_part)

    filter1 = Filter(should_pass_part = lambda part: part.quality >= 0.75)
    filter2 = Filter(should_pass_part = lambda part: part.quality < 0.75)

    M2 = Machine('PartFixer', upstream = [filter2], cycle_time = 1)
    M2.add_finish_processing_callback(improve_part)
    filter1.upstream = [M1, M2]
    filter2.upstream = [M1, M2]

    sink = Sink(upstream = [filter1], collect_parts = True)

    system = System([source, sink, M1, M2, filter1, filter2], DataStorageType.MEMORY)
    random.seed(1)
    system.simulate(simulation_time = 1000)
    print_produced_parts_and_average_quality(system, [M1, M2])


if __name__ == '__main__':
    main()

