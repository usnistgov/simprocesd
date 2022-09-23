''' This example simulates a simple manufacturing setup where the
machines accrue damage over time which negatively impacts the quality of
the parts those machines produce. Simulation data is then reviewed.
'''
import random
import sys

from simprocesd.model import System
from simprocesd.model.factory_floor import Machine, Source, Buffer, Sink, Part, Maintainer
from simprocesd.model.sensors import PeriodicSensor, Probe
from simprocesd.utils import geometric_distribution_sample, plot_throughput, \
    plot_damage, plot_value, print_produced_parts_and_average_quality, simple_plot

from . import StatusTrackerWithDamage


def process_part(part, status):
    quality_change = 1 - status.damage * (0.1 + random.uniform(-.01, .01))
    part.quality += quality_change
    if quality_change > 0:
        part.add_value('part_processed', quality_change * 10)


def new_machine(name, upstream, cycle_time, probability_to_degrade, maintainer):
    time_to_maintain = lambda tag: geometric_distribution_sample(0.25, 25)
    status = StatusTrackerWithDamage(60, probability_to_degrade, 1, 3,
                                     get_time_to_maintain = time_to_maintain,
                                     get_capacity_to_maintain = lambda tag: 1)
    machine = Machine(name, upstream, cycle_time, status)
    machine.add_finish_processing_callback(lambda p, st = status: process_part(p, st))
    machine.add_failed_callback(lambda p, m = machine: maintainer.request_maintenance(m))
    return machine


def main(is_test = False):
    system = System()
    maintainer = Maintainer(capacity = 1)

    sample_part = Part('Part', value = 1, quality = 0)
    source = Source('source', sample_part, cycle_time = 1)
    buffer = Buffer('source_buffer', [source], capacity = 12)
    M1 = new_machine('M1', [buffer], 2.5, 0.15, maintainer)
    M2 = new_machine('M2', [buffer], 2.5, 0.3, maintainer)
    M3 = new_machine('M3', [buffer], 2.5, 0.6, maintainer)
    sink = Sink('sink', [M1, M2, M3])

    level_probe = Probe(lambda target: target.level(), buffer)
    sensor = PeriodicSensor(2.5, [level_probe])

    system.simulate(simulation_duration = 60 * 24 * 7)

    # Print information to console.
    print(f'\nFinal net value of machines: {round(system.get_net_value_of_assets(), 2)}')
    print_produced_parts_and_average_quality(system, [M1, M2, M3])

    if not is_test:
        # Show graphs.
        plot_throughput(system, [M1, M2, M3])
        plot_damage(system, [M1, M2, M3])
        # Source produces parts and reduces its own value by the value of produced parts.
        # Sink collects parts and increases its own value by the value of collected parts.
        plot_value([source, sink])
        # Show data from custom sensor.
        simple_plot(sensor.data['time'], sensor.data[level_probe],
                    "Parts in Buffer", 'time', 'parts')


if __name__ == '__main__':
    main(len(sys.argv) > 1 and sys.argv[1] == 'testing')
