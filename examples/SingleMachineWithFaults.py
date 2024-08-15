'''An example with a custom PartProcessor that can exhibit recurring
faults (MachineWithFaults).
Once the machine experiences a fault it will shut down and stop
receiving and processing parts until maintained.

Expected to produce about 4000-4200 parts.
Expected uptime %: ~80%
    - average time to break 40, average maintenance duration 10
Expected productive %: slightly above 50%
    - source cycle time is 2 and processor cycle time is 1
'''

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Sink, Maintainer
from simprocesd.utils import geometric_distribution_sample

from machine_with_faults import MachineWithFaults


def main():
    schedule_repair = lambda machine, fault: maintainer.create_work_order(machine, fault)
    system = System()
    maintainer = Maintainer()

    source = Source(cycle_time = 2)
    M1 = MachineWithFaults('M1', cycle_time = 1, upstream = [source])
    M1.add_recurring_fault('Fault',
        get_time_to_fault = lambda: geometric_distribution_sample(0.1, 4),
        get_time_to_maintain = lambda: geometric_distribution_sample(0.1, 1),
        failed_callback = schedule_repair)

    sink = Sink(upstream = [M1])

    # If time units are minutes then simulation period is a week.
    total_time = 60 * 24 * 7
    system.simulate(simulation_duration = total_time)

    percent_uptime = (M1.uptime / total_time) * 100
    percent_utilization = (M1.utilization_time / M1.uptime) * 100
    print(f'Machine {M1.name} uptime % of total simulation time: {percent_uptime:.2f}%')
    print(f'Machine {M1.name} productive time as % of uptime: {percent_utilization:.2f}%')


if __name__ == '__main__':
    main()
