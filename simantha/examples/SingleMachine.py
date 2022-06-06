''' Expected parts produced: 100.
'''

from simantha.model import System
from simantha.model.factory_floor import Source, Machine, Sink, Part


def main():
    # System needs to be created first so that other simulation objects can
    # register themselves with it automatically.
    system = System()
    # System object automatically.
    source = Source(sample_part = Part())
    M1 = Machine(upstream = [source], cycle_time = 1)
    sink = Sink(upstream = [M1])

    system.simulate(simulation_time = 100)
    print(f'Sink received {sink.received_parts_count} parts.')


if __name__ == '__main__':
    main()
