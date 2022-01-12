'''
An example of Markovian degradation of a single machine. Once the machine
reaches the zero health it will shut down and stop receiving and processing
parts.
'''

import random

from ..model.factory_floor import Source, Machine, Sink
from ..model import System
from ..utils import geometric_distribution_sample


def main():
    source = Source()
    M1 = Machine('M1',
                 cycle_time = 1,
                 upstream = [source])
    M1.status_tracker.add_recurring_fault(
        get_time_to_fault = lambda: geometric_distribution_sample(1, 4))
    sink = Sink(upstream = [M1])

    system = System([source, M1, sink])

    random.seed(1)
    # If time units are minutes then simulation period is a day.
    # The machine will fail part way through and stop producing parts.
    system.simulate(simulation_time = 60 * 24)


if __name__ == '__main__':
    main()
