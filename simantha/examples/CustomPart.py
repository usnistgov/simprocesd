import random

from .. import Part, Source, Machine, Buffer, Sink, System, MachineStatus


class CustomStatus(MachineStatus):

    def __init__(self, quality_distribution):
        # Quality distribution should return a value on [0, 1]
        self.quality_distribution = quality_distribution

    def finished_processing_part(self, part):
        part.quality *= self.quality_distribution()


def main():
    source = Source(sample_part = Part(quality = 1.0))
    M1 = Machine('M1',
                 upstream = [source],
                 # Part quality distribution [0.9, 1.0]
                 machine_status = CustomStatus(lambda: 1 - 0.1 * random.random()),
                 cycle_time = 1)
    B1 = Buffer('B1', upstream = [M1], capacity = 10)
    M2 = Machine('M2',
                 upstream = [B1],
                 # Part quality distribution [0.6, 0.8]
                 machine_status = CustomStatus(lambda: 0.8 - 0.2 * random.random()),
                 cycle_time = 2)
    M3 = Machine('M3',
                 upstream = [B1],
                 # Part quality distribution [0.3, 0.6]
                 machine_status = CustomStatus(lambda: 0.6 - 0.3 * random.random()),
                 cycle_time = 2)
    sink = Sink(upstream = [M2, M3], collect_parts = True)

    system = System([source, M1, B1, M2, M3, sink])

    random.seed(1)
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
