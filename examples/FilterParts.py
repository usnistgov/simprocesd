''' Expected parts received by sink: 999-1000
Processor should have received 1000 parts.
PartFixer should have received about 750 parts.
Processor average output part quality should be around 0.5
PartFixer average output part quality should be between 0.9 and 1
'''
import random

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, PartProcessor, Sink, DecisionGate
from simprocesd.utils import print_produced_parts_and_average_quality


def process_part(machine, part):
    part.quality = random.random()


def improve_part(machine, part):
    part.quality = min(1, part.quality + 0.75)


def main():
    system = System()

    source = Source()
    M1 = PartProcessor('Processor', upstream = [source], cycle_time = 1)
    M1.add_finish_processing_callback(process_part)
    # DecisionGate conditions are setup so that processed parts can
    # always pass at least one of them, otherwise parts may get stuck in the
    # processor preventing it from working on new parts.
    gate1 = DecisionGate(upstream = [M1], decider_override = lambda gate, part: part.quality >= 0.75)
    gate2 = DecisionGate(upstream = [M1], decider_override = lambda gate, part: part.quality < 0.75)

    M2 = PartProcessor('PartFixer', upstream = [gate2], cycle_time = 1)
    M2.add_finish_processing_callback(improve_part)

    sink = Sink(upstream = [gate1, M2], collect_parts = True)

    random.seed(1)
    system.simulate(simulation_duration = 1000)
    print_produced_parts_and_average_quality(system, [M1, M2])


if __name__ == '__main__':
    main()

