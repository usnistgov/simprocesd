''' Expected parts produced: around 6500-7000
'''

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Machine, Sink, Buffer, Maintainer
from simprocesd.utils import geometric_distribution_sample

from . import StatusTrackerWithFaults


def main():
    # 10% degradation rate with a starting health of 4.
    get_ttf = lambda: geometric_distribution_sample(.1, 4)
    # Every time unit there is 10% chance to fix the machine.
    get_ttm = lambda: geometric_distribution_sample(.1, 1)

    system = System()

    maintainer = Maintainer()
    schedule_repair = lambda f: maintainer.request_maintenance(
            f.machine, f.name)

    source = Source()
    M1 = Machine('M1', upstream = [source], cycle_time = 1,
                 status_tracker = StatusTrackerWithFaults())
    M1.status_tracker.add_recurring_fault(get_time_to_fault = get_ttf,
                                          get_time_to_maintain = get_ttm,
                                          failed_callback = schedule_repair)
    B1 = Buffer(upstream = [M1], capacity = 5)
    M2 = Machine('M2', upstream = [B1], cycle_time = 1,
                 status_tracker = StatusTrackerWithFaults())
    M2.status_tracker.add_recurring_fault(get_time_to_fault = get_ttf,
                                          get_time_to_maintain = get_ttm,
                                          failed_callback = schedule_repair)
    sink = Sink(upstream = [M2])

    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)


if __name__ == '__main__':
    main()
