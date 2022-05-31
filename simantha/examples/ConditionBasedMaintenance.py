'''
Example of a condition-based maintenance policy. The CBM threshold determines the health
index level at which a machine requests maintenance.
Expected parts received by sink: around 4400.
Each machine should have been maintained about 300 times.
'''
import random

from simantha.examples import StatusTrackerWithDamage
from simantha.model import System
from simantha.model.cms import Cms
from simantha.model.factory_floor import Source, Machine, Buffer, Sink, Maintainer
from simantha.model.sensors import PeriodicSensor, AttributeProbe
from simantha.utils import DataStorageType, geometric_distribution_sample, print_maintenance_counts


def time_to_maintain(damage):
    if damage < 4:
        # maintenance before machine failure
        return geometric_distribution_sample(0.25, 1)
    else:
        # maintenance for a failed machine
        return geometric_distribution_sample(0.10, 1)


class CustomCms(Cms):

    def on_sense(self, sensor, time, data):
        if data[0] >= 3:
            # Request preventative maintenance
            self.maintainer.request_maintenance(sensor.probes[0].target.machine)


def main():

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
    cms = CustomCms(maintainer, name = 'CMS')

    p1 = AttributeProbe('damage', status1)
    sensor1 = PeriodicSensor(1, [p1], name = 'M1 Sensor')
    cms.add_sensor(sensor1)
    p2 = AttributeProbe('damage', status2)
    sensor2 = PeriodicSensor(1, [p2], name = 'M2 Sensor')
    cms.add_sensor(sensor2)

    system = System([source, M1, B1, M2, sink, cms], DataStorageType.MEMORY)

    random.seed(1)
    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_time = 60 * 24 * 7)

    print_maintenance_counts(system)


if __name__ == '__main__':
    main()
