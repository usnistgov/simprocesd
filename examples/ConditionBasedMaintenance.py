'''
Example of a condition-based maintenance policy. The CBM threshold
determines the health index level at which a machine requests
maintenance.
Expected parts received by sink: around 4400.
Each machine should have been maintained about 300 times.
'''

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Buffer, Sink, Maintainer
from simprocesd.model.sensors import PeriodicSensor, AttributeProbe
from simprocesd.utils import geometric_distribution_sample, print_finished_work_order_counts

from .machine_with_damage import MachineWithDamage


def time_to_maintain(machine, tag):
    if machine.damage < 4:
        # maintenance before machine failure
        return geometric_distribution_sample(0.25, 1)
    else:
        # maintenance for a failed machine
        return geometric_distribution_sample(0.10, 1)


def main():
    system = System()

    source = Source()
    M1 = MachineWithDamage(name = 'M1',
                           upstream = [source],
                           cycle_time = 1,
                           period_to_degrade = 1,
                           probability_to_degrade = 0.1,
                           damage_on_degrade = 1,
                           damage_to_fail = 4,
                           get_maintenance_duration = time_to_maintain,
                           get_capacity_to_maintain = lambda m, t: 1
    )
    B1 = Buffer(upstream = [M1], capacity = 10)
    M2 = MachineWithDamage(name = 'M2',
                           upstream = [B1],
                           cycle_time = 2,
                           period_to_degrade = 1,
                           probability_to_degrade = 0.1,
                           damage_on_degrade = 1,
                           damage_to_fail = 4,
                           get_maintenance_duration = time_to_maintain,
                           get_capacity_to_maintain = lambda m, t: 1
    )
    sink = Sink(upstream = [M2])

    maintainer = Maintainer(capacity = 1)

    def on_sense(sensor, time, data):
        # Preventative maintenance at 3 damage. Machines are
        # configured to fail at 4 damage.
        if data[0] >= 3:
            device = sensor.probes[0].target
            maintainer.create_work_order(device)

    p1 = AttributeProbe('damage', M1)
    sensor1 = PeriodicSensor(1, [p1], name = 'M1 Sensor')
    sensor1.add_on_sense_callback(on_sense)

    p2 = AttributeProbe('damage', M2)
    sensor2 = PeriodicSensor(1, [p2], name = 'M2 Sensor')
    sensor2.add_on_sense_callback(on_sense)

    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)

    print_finished_work_order_counts(system)


if __name__ == '__main__':
    main()
