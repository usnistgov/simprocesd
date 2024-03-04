''' Expected parts produced: 99.
Simple setup where parts are created by the Source, pass through one
PartProcessor, and are collected by the Sink.
'''

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, PartProcessor, Sink, PartGenerator


def main():
    # System needs to be created first so that other simulation objects
    # can register themselves with it automatically.
    system = System()
    # Source will create a new Part every 1 time unit.
    source = Source(part_generator = PartGenerator(name_prefix = 'DefaultPart'),
                    cycle_time = 1)
    # Create a part processor that gets parts from source and takes
    # 1 time unit to process the part.
    M1 = PartProcessor(upstream = [source], cycle_time = 1)
    sink = Sink(upstream = [M1])

    # Time units are not defined and can be anything as long as the
    # same units are used throughout the simulation.
    system.simulate(simulation_duration = 100)


if __name__ == '__main__':
    main()
