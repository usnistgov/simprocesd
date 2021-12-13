import random

from .. import Source, Machine, Buffer, Sink, System
from ..components.machine_status import MachineStatus
from ..maintainer import Maintainer
from ..math_utils import geometric_distribution_sample


def main():
    # 10% degradation rate with a starting health of 4.
    get_ttf = lambda: geometric_distribution_sample(10, 4)
    # Maintenance time is using a normal distribution with a mean of 7.
    get_ttr = lambda: random.normalvariate(7, 1)

    maintainer = Maintainer()
    schedule_repair = lambda f: maintainer.request_maintenance(
            f.machine, f.get_time_to_repair(), f.capacity_to_repair)

    status1 = MachineStatus()
    status1.add_failure(get_time_to_failure = get_ttf,
                        get_time_to_repair = get_ttr,
                        failed_callback = schedule_repair)
    status2 = MachineStatus()
    status2.add_failure(get_time_to_failure = get_ttf,
                        get_time_to_repair = get_ttr,
                        failed_callback = schedule_repair)

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
