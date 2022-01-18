import random

from ..model.factory_floor import Source, Machine, Sink, Buffer, Maintainer
from ..model import System
from ..utils import geometric_distribution_sample
from . import StatusTrackerWithFaults


def main():
    # 10% degradation rate with a starting health of 4.
    get_ttf = lambda: geometric_distribution_sample(10, 4)
    # Maintenance time is using a normal distribution with a mean of 7.
    get_ttr = lambda: random.normalvariate(7, 1)

    maintainer = Maintainer()
    schedule_repair = lambda f: maintainer.request_maintenance(
            f.machine, f.name)

    source = Source()
    M1 = Machine('M1', upstream = [source], cycle_time = 1,
                 status_tracker = StatusTrackerWithFaults())
    M1.status_tracker.add_recurring_fault(get_time_to_fault = get_ttf,
                                          get_time_to_repair = get_ttr,
                                          failed_callback = schedule_repair)
    B1 = Buffer(upstream = [M1], capacity = 5)
    M2 = Machine('M2', upstream = [B1], cycle_time = 1,
                 status_tracker = StatusTrackerWithFaults())
    M2.status_tracker.add_recurring_fault(get_time_to_fault = get_ttf,
                                          get_time_to_repair = get_ttr,
                                          failed_callback = schedule_repair)
    sink = Sink(upstream = [M2])

    system = System([source, M1, B1, M2, sink, maintainer])

    random.seed(1)
    # If time units are minutes then simulation period is a day.
    system.simulate(simulation_time = 60 * 24)


if __name__ == '__main__':
    main()
