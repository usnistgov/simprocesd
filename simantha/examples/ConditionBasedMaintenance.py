'''
Example of a condition-based maintenance policy. The CBM threshold determines the health
index level at which a machine requests maintenance.
Expected parts produced: around 4400.
'''
import random

from ..model import System
from ..model.cms import Cms
from ..model.factory_floor import Source, Machine, Buffer, Sink, Maintainer
from ..model.sensors import PeriodicSensor, AttributeProbe
from ..utils import geometric_distribution_sample
from .status_tracker_with_damage import StatusTrackerWithDamage


def time_to_maintain(damage):
    if damage < 4:
        # maintenance before machine failure
        return geometric_distribution_sample(0.25, 1)
    else:
        # maintenance for a failed machine
        return geometric_distribution_sample(0.10, 1)


class CustomCms(Cms):

    def on_sense_damage(self, machine, damage):
        if damage >= 3:
            # Request preventative maintenance
            self.maintainer.request_maintenance(machine)


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
    sensor1 = PeriodicSensor(M1, 1, [p1], name = 'M1 Sensor')
    sensor1.add_on_sense_callback(lambda time, data: cms.on_sense_damage(M1, data[0]))
    cms.add_sensor(sensor1)
    p2 = AttributeProbe('damage', status2)
    sensor2 = PeriodicSensor(M2, 1, [p2], name = 'M2 Sensor')
    sensor2.add_on_sense_callback(lambda time, data: cms.on_sense_damage(M2, data[0]))
    cms.add_sensor(sensor2)

    system = System(objects = [source, M1, B1, M2, sink, cms])

    random.seed(1)
    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_time = 60 * 24 * 7)


if __name__ == '__main__':
    main()
