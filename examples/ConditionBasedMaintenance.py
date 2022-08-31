'''
Example of a condition-based maintenance policy. The CBM threshold
determines the health index level at which a machine requests
maintenance.
Expected parts received by sink: around 4400.
Each machine should have been maintained about 300 times.
'''
import random

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Machine, Buffer, Sink, Maintainer
from simprocesd.model.sensors import PeriodicSensor, AttributeProbe
from simprocesd.utils import DataStorageType, geometric_distribution_sample, print_maintenance_counts

from . import StatusTrackerWithDamage


def time_to_maintain(damage):
    if damage < 4:
        # maintenance before machine failure
        return geometric_distribution_sample(0.25, 1)
    else:
        # maintenance for a failed machine
        return geometric_distribution_sample(0.10, 1)


def main():
    system = System(DataStorageType.MEMORY)

    status1 = StatusTrackerWithDamage(1, 0.1, 1, 4,
                                      get_time_to_maintain = time_to_maintain,
                                      get_capacity_to_maintain = lambda d: 1)
    status2 = StatusTrackerWithDamage(1, 0.1, 1, 4,
                                      get_time_to_maintain = time_to_maintain,
                                      get_capacity_to_maintain = lambda d: 1)

    source = Source()
    M1 = Machine(
        name = 'M1',
        upstream = [source],
        cycle_time = 1,
        status_tracker = status1
    )
    B1 = Buffer(upstream = [M1], capacity = 10)
    M2 = Machine(
        name = 'M2',
        upstream = [B1],
        cycle_time = 2,
        status_tracker = status2
    )
    sink = Sink(upstream = [M2])

    maintainer = Maintainer(capacity = 1)

    def on_sense(sensor, time, data):
        if data[0] >= 3:
            # probe target is the MachineStatusTracker
            device = sensor.probes[0].target.machine
            # Request  maintenance.
            maintainer.request_maintenance(device)

    p1 = AttributeProbe('damage', status1)
    sensor1 = PeriodicSensor(1, [p1], name = 'M1 Sensor')
    sensor1.add_on_sense_callback(on_sense)

    p2 = AttributeProbe('damage', status2)
    sensor2 = PeriodicSensor(1, [p2], name = 'M2 Sensor')
    sensor2.add_on_sense_callback(on_sense)

    random.seed(1)
    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)

    print_maintenance_counts(system)


if __name__ == '__main__':
    main()
