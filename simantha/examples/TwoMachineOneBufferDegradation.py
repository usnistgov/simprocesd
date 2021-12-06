import random

from .. import Source, Machine, Buffer, Sink, System
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
    M1 = Machine('M1', upstream = [source], machine_status = status, cycle_time = 1)
    B1 = Buffer(upstream = [M1], capacity = 5)
    M2 = Machine(name = 'M2', upstream = [B1], machine_status = status, cycle_time = 1)
    sink = Sink(upstream = [M2])

    system = System([source, M1, B1, M2, sink])

    random.seed(10)
    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_time = 60 * 24 * 7)


if __name__ == '__main__':
    main()
