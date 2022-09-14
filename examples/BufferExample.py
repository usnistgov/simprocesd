''' Expected parts produced: 10079
'''
from simprocesd.model import System
from simprocesd.model.factory_floor import Buffer, Machine, Part, Sink, Source


def main():
    system = System()

    source = Source(sample_part = Part())
    M1 = Machine(upstream = [source], cycle_time = 1)
    B1 = Buffer(upstream = [M1], capacity = 5)
    M2 = Machine(upstream = [B1], cycle_time = 1)
    sink = Sink(upstream = [M2])

    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)


if __name__ == '__main__':
    main()
