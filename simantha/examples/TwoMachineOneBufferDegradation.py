import random

from .. import Source, Machine, Buffer, Sink, System
from ..components.machine_status import PeriodicFailStatus
from ..maintainer import Maintainer


class CustomStatus(PeriodicFailStatus):

    def __init__(self, maintainer, **kwargs):
        super().__init__(**kwargs)
        self.maintainer = maintainer

    def failed(self):
        self.maintainer.request_maintenance(self._machine, 1)


def calculate_ttf():
    degradation_rate_percentage = 10
    starting_health = 4
    ttf = 0
    while starting_health > 0:
        ttf += 1
        if random.uniform(0, 100) <= degradation_rate_percentage:
            starting_health -= 1
    return ttf


def get_time_to_fix():
    return 10


def main():
    maintainer = Maintainer()
    status1 = CustomStatus(maintainer,
                           get_time_to_failure = calculate_ttf,
                           get_time_to_fix = get_time_to_fix)
    status2 = CustomStatus(maintainer,
                           get_time_to_failure = calculate_ttf,
                           get_time_to_fix = get_time_to_fix)

    source = Source()
    M1 = Machine('M1', upstream = [source], machine_status = status1, cycle_time = 1)
    B1 = Buffer(upstream = [M1], capacity = 5)
    M2 = Machine(name = 'M2', upstream = [B1], machine_status = status2, cycle_time = 1)
    sink = Sink(upstream = [M2])

    system = System([source, M1, B1, M2, sink], maintainer)

    random.seed(1)
    # If time units are minutes then simulation period is a day.
    system.simulate(simulation_time = 60 * 24)


if __name__ == '__main__':
    main()
