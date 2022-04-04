''' This example simulates a simple manufacturing setup where the
machines accrue damage over time which negatively impacts the quality of
the parts those machines produce. Simulation data is then reviewed.
'''
import random

from . import StatusTrackerWithDamage
from ..model import System
from ..model.factory_floor import Machine, Source, Buffer, Sink, Part, Maintainer, \
    PartHandlingDevice, FlowOrder
from ..model.sensors import PeriodicSensor, Probe
from ..utils import DataStorageType, geometric_distribution_sample, plot_throughput, \
    plot_damage, plot_value, print_produced_parts_and_average_quality, simple_plot


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
    machine.add_failed_callback(lambda m = machine: maintainer.request_maintenance(m))
    return machine


def main():
    maintainer = Maintainer(capacity = 1)

    source = Source('source', Part('Part', value = 1, quality = 0), time_to_produce_part = 1)
    buffer = Buffer('source_buffer', [source], capacity = 12)
    phd = PartHandlingDevice(upstream = [buffer], flow_order = FlowOrder.RANDOM)
    M1 = new_machine('M1', [phd], 2.5, 0.15, maintainer)
    M2 = new_machine('M2', [phd], 2.5, 0.3, maintainer)
    M3 = new_machine('M3', [phd], 2.5, 0.6, maintainer)
    sink = Sink('sink', [M1, M2, M3])
    # Add a custom sensor to buffer with a single probe that measures buffer level.
    level_probe = Probe(lambda target: target.level(), buffer)
    sensor = PeriodicSensor(buffer, 2.5, [level_probe])

    system = System([maintainer, source, buffer, M1, M2, M3, phd, sink, sensor],
                    DataStorageType.MEMORY)
    random.seed(10)  # Setting seed ensures same results every run.
    system.simulate(simulation_time = 60 * 24 * 7)

    # Print information to console.
    print(f'\nFinal net value of machines: {round(system.get_net_value_of_objects(), 2)}')
    print_produced_parts_and_average_quality(system, [M1, M2, M3])
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
    main()
