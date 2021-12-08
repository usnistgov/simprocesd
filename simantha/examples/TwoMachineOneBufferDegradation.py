import random

from .. import Source, Machine, Buffer, Sink, System
from ..components.machine_status import PeriodicFailStatus
from ..maintainer import Maintainer
from ..math_utils import geometric_distribution_sample


def main():
    # 10% degradation rate with a starting health of 4.
    get_ttf = lambda: geometric_distribution_sample(10, 4)
    # Maintenance takes 5-8 long.
    get_ttr = lambda: random.uniform(5, 8)

    maintainer = Maintainer()
    status1 = PeriodicFailStatus(get_time_to_failure = get_ttf, get_time_to_fix = get_ttr)
    status1.set_failed_callback(
        lambda: maintainer.request_maintenance(status1.machine, 1))
    status2 = PeriodicFailStatus(get_time_to_failure = get_ttf, get_time_to_fix = get_ttr)
    status2.set_failed_callback(
        lambda: maintainer.request_maintenance(status2.machine, 1))

    source = Source()
    M1 = Machine('M1', upstream = [source], machine_status = status1, cycle_time = 1)
    B1 = Buffer(upstream = [M1], capacity = 5)
    M2 = Machine('M2', upstream = [B1], machine_status = status2, cycle_time = 1)
    sink = Sink(upstream = [M2])

    system = System([source, M1, B1, M2, sink, maintainer])

    random.seed(1)
    # If time units are minutes then simulation period is a day.
    system.simulate(simulation_time = 60 * 24)


if __name__ == '__main__':
    main()
