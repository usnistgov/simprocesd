import random

from .. import Source, Machine, Sink, System, Part
from ..components.machine_status import MachineStatus
from ..maintainer import Maintainer

''' Time units are seconds and value is in dollars.
Machine produces 10 items per second but we will have each Part represent 50 items in
order to speed up the simulation.
'''
count_per_part = 50
processing_rate = 10
machine_cycle_time = count_per_part / processing_rate
# Machine operates an average of 4.1667 hours per day
operating_time_per_day = 60 * 60 * 4.1667


def wasted_part_processing(part):
    part.value = 0
    part.quality = 0


def default_part_processing(part):
    part.value = 1.5 * count_per_part * part.quality


def main():
    random.seed(1)
    # Working year; 5 days a week and 50 weeks a year.
    duration = operating_time_per_day * 5 * 50

    no_cms_net = no_cms(duration)
    print(f'Net value without CMS: ${no_cms_net}')
    with_cms_net = with_cms(duration)
    print(f'Net value with CMS: ${with_cms_net}')
    print(f'Yearly operational profit of using a CMS is: ${with_cms_net - no_cms_net}')


def no_cms(duration):
    part = Part('50xPart', 0, 1)

    maintainer = Maintainer()
    schedule_repair = lambda f: maintainer.request_maintenance(
            f.machine, f.name, f.get_time_to_repair())

    status = MachineStatus()
    status.set_finish_processing_callback(default_part_processing)
    status.add_failure(name = 'Dulling',
                        # Failure rate of 100 days.
                        get_time_to_failure = lambda: 100 * operating_time_per_day,
                        get_time_to_repair = lambda: 300 / processing_rate,
                        get_cost_to_fix = lambda: 100,
                        is_hard_failure = False,
                        failed_callback = schedule_repair,
                        finish_processing_callback = wasted_part_processing)
    status.add_failure(name = 'Misalignment',
                        # Failure rate 99% per day.
                        get_time_to_failure = lambda: 1.01 * operating_time_per_day,
                        get_time_to_repair = lambda: 500 / processing_rate,
                        get_cost_to_fix = lambda: 75,
                        is_hard_failure = False,
                        failed_callback = schedule_repair,
                        finish_processing_callback = wasted_part_processing)

    source = Source(sample_part = part)
    M1 = Machine('M1', upstream = [source], machine_status = status,
                 cycle_time = machine_cycle_time)
    sink = Sink(upstream = [M1])

    system = System([source, M1, sink, maintainer])

    system.simulate(duration)
    return system.get_net_value()


def with_cms(duration):
    part = Part('50xPart', 0, 1)

    maintainer = Maintainer()
    schedule_repair = lambda f: maintainer.request_maintenance(
            f.machine, f.name, f.get_time_to_repair())

    status = MachineStatus()
    status.set_finish_processing_callback(default_part_processing)
    status.add_failure(name = 'Detected Dulling',
                        # Failure rate of 100 days.
                        get_time_to_failure = lambda: 106.383 * operating_time_per_day,
                        get_time_to_repair = lambda: 100 / processing_rate,
                        get_cost_to_fix = lambda: 100,
                        is_hard_failure = False,
                        failed_callback = schedule_repair,
                        finish_processing_callback = wasted_part_processing)
    status.add_failure(name = 'Missed Dulling',
                        # Failure rate of 100 days.
                        get_time_to_failure = lambda: 10000 * operating_time_per_day,
                        get_time_to_repair = lambda: 300 / processing_rate,
                        get_cost_to_fix = lambda: 100,
                        is_hard_failure = False,
                        failed_callback = schedule_repair,
                        finish_processing_callback = wasted_part_processing)
    status.add_failure(name = 'FalseAlert Dulling',
                        # Failure rate of 100 days.
                        get_time_to_failure = lambda: 2000 * operating_time_per_day,
                        get_cost_to_fix = lambda: 85,
                        is_hard_failure = False,
                        failed_callback = schedule_repair)
    status.add_failure(name = 'Detected Misalignment',
                        # Failure rate 99% per day.
                        get_time_to_failure = lambda: 1.0213 * operating_time_per_day,
                        get_time_to_repair = lambda: 150 / processing_rate,
                        get_cost_to_fix = lambda: 75,
                        is_hard_failure = False,
                        failed_callback = schedule_repair,
                        finish_processing_callback = wasted_part_processing)
    status.add_failure(name = 'Missed Misalignment',
                        # Failure rate 99% per day.
                        get_time_to_failure = lambda: 1000 * operating_time_per_day,
                        get_time_to_repair = lambda: 500 / processing_rate,
                        get_cost_to_fix = lambda: 75,
                        is_hard_failure = False,
                        failed_callback = schedule_repair,
                        finish_processing_callback = wasted_part_processing)
    status.add_failure(name = 'FalseAlert Misalignment',
                        # Failure rate 99% per day.
                        get_time_to_failure = lambda: 2000 * operating_time_per_day,
                        get_cost_to_fix = lambda: 85,
                        is_hard_failure = False,
                        failed_callback = schedule_repair)

    source = Source(sample_part = part)
    M1 = Machine('M1', upstream = [source], machine_status = status,
                 cycle_time = machine_cycle_time)
    sink = Sink(upstream = [M1])

    system = System([source, M1, sink, maintainer])

    system.simulate(duration)
    return system.get_net_value()


if __name__ == '__main__':
    main()
