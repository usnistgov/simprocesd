"""
An example of Markovian degradation of a single machine. Once the machine
reaches the zero health it will shut down and stop receiving and processing
parts.
"""

import random

from .. import Source, Machine, Sink, System
from ..components.machine_status import PeriodicFailStatus


def calculate_ttf():
    degradation_rate_percentage = 1
    starting_health = 4
    ttf = 0
    while starting_health > 0:
        ttf += 1
        if random.uniform(0, 100) <= degradation_rate_percentage:
            starting_health -= 1
    return ttf


def main():
    source = Source()
    status = PeriodicFailStatus(calculate_ttf)
    M1 = Machine('M1',
                 cycle_time = 1,
                 upstream = [source],
                 machine_status = status)
    sink = Sink(upstream = [M1])

    system = System([source, M1, sink])

    random.seed(1)
    # If time units are minutes then simulation period is a day.
    # The machine will fail part way through and stop producing parts.
    system.simulate(simulation_time = 60 * 24)


if __name__ == '__main__':
    main()
