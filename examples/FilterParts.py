''' Expected parts received by sink: 999-1000
Processor should have received 1000 parts.
PartFixer should have received about 750 parts.
Processor average output part quality should be around 0.5
PartFixer average output part quality should be between 0.9 and 1
'''
import random

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Machine, Sink, DecisionGate
from simprocesd.utils import DataStorageType, print_produced_parts_and_average_quality


def process_part(machine, part):
    part.quality = random.random()


def improve_part(machine, part):
    part.quality = min(1, part.quality + 0.75)


def main():
    system = System(DataStorageType.MEMORY)

    source = Source()
    M1 = Machine('Processor', upstream = [source], cycle_time = 1)
    M1.add_finish_processing_callback(process_part)

    gate1 = DecisionGate(should_pass_part = lambda part: part.quality >= 0.75)
    gate2 = DecisionGate(should_pass_part = lambda part: part.quality < 0.75)

    M2 = Machine('PartFixer', upstream = [gate2], cycle_time = 1)
    M2.add_finish_processing_callback(improve_part)
    gate1.set_upstream([M1, M2])
    gate2.set_upstream([M1, M2])

    sink = Sink(upstream = [gate1], collect_parts = True)

    random.seed(1)
    system.simulate(simulation_duration = 1000)
    print_produced_parts_and_average_quality(system, [M1, M2])


if __name__ == '__main__':
    main()

