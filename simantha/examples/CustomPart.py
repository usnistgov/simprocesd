import random

from ..model import System
from ..model.factory_floor import Part, Source, Machine, Buffer, Sink


def update_quality(part, min_, max_, mac):
    diff = max_ - min_
    part.quality *= max_ - diff * random.random()


def main():
    source = Source(sample_part = Part(quality = 1.0))
    M1 = Machine('M1',
                 upstream = [source],
                 cycle_time = 1)
    M1.status_tracker.add_finish_processing_callback(lambda p: update_quality(p, 0.9, 1, 'M1'))
    B1 = Buffer('B1', upstream = [M1], capacity = 10)
    M2 = Machine('M2',
                 upstream = [B1],
                 cycle_time = 2)
    M2.status_tracker.add_finish_processing_callback(lambda p: update_quality(p, 0.6, 0.8, 'M2'))
    M3 = Machine('M3',
                 upstream = [B1],
                 cycle_time = 2)
    M3.status_tracker.add_finish_processing_callback(lambda p: update_quality(p, 0.3, 0.6, 'M3'))
    sink = Sink(upstream = [M2, M3], collect_parts = True)

    system = System([source, M1, B1, M2, M3, sink])

    random.seed(1)
    # If time units are minutes then simulation period is a day.
    system.simulate(simulation_time = 24 * 60)

    print('\nAverage final quality of the parts that passed through each machine:')
    for machine in [M1, M2, M3]:
        machine_parts = [
            part for part in sink.collected_parts if machine.name in part.routing_history
        ]
        average_quality = (
            sum([part.quality for part in machine_parts]) / len(machine_parts)
        )
        print(f'{machine.name} average quality: {average_quality:.2%}')


if __name__ == '__main__':
    main()
