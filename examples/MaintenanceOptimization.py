'''
Example for quantifying the impact of different
Condition Based Maintenance (CBM) policies.

Setup: there are 5 machines in parallel that accrue damage over time
which negatively affects the part quality (0-1). Only parts of quality
min_acceptable_quality and higher are considered good/acceptable.
'''
import random
import statistics
import sys

from matplotlib import pyplot

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Sink, Maintainer, Part
from simprocesd.utils import DataStorageType

from .machine_with_damage import MachineWithDamage

# Setup parameters
capacity_to_repair = 1
maintainer_capacity = 2
time_to_repair = 150
cycle_time = 5
min_acceptable_quality = 0.9
# Machine damage parameters.
d_period, d_probability, d_magnitude, d_fail = 60, 0.33, .5, 5
# Simulation duration per iteration. 1 week (12 operational hours a day).
simulation_duration = 60 * 12 * 7
# Iterations per threshold.
iterations = 10

damage_threshold = 0


def main(is_test = False):
    global iterations, damage_threshold
    if is_test:
        # Reduce example runtime during testing.
        iterations = 1

    system = System(DataStorageType.MEMORY)
    # Setup the experiment.
    maintainer = Maintainer(capacity = maintainer_capacity)
    source = Source('Source', Part(quality = 1), 1)
    M1 = generate_machine('M1', [source], maintainer)
    M2 = generate_machine('M2', [source], maintainer)
    M3 = generate_machine('M3', [source], maintainer)
    M4 = generate_machine('M4', [source], maintainer)
    M5 = generate_machine('M5', [source], maintainer)
    all_machines = [M1, M2, M3, M4, M5]
    sink = Sink('Sink', all_machines, collect_parts = True)

    print('Running simulations...')
    results = []
    # Damage thresholds to test and plot.
    thresholds = [x * d_magnitude for x in range(1, round((d_fail / d_magnitude)) + 1)]
    for current_threshold in thresholds:
        damage_threshold = current_threshold
        results.append([])
        for i in range(iterations):
            system.simulate(simulation_duration = simulation_duration, print_summary = False)
            results[-1].append([x.quality for x in sink.collected_parts])
            system.simulate(simulation_duration = 0, print_summary = False, reset = True)

    # Prepare data for graphing.
    all_parts_per_dt = []
    for dt in results:
        all_parts_per_dt.append([])
        for res in dt:
            all_parts_per_dt[-1] += res

    all_parts_counts = [len(dt) / len(results[0]) for dt in all_parts_per_dt]
    good_parts_counts = [len([x for x in dt if x >= min_acceptable_quality]) / len(results[0])
                         for dt in all_parts_per_dt]
    bad_parts_counts = [all_parts_counts[i] - good_parts_counts[i] for i in
                        range(len(all_parts_counts))]
    quality_all_parts = [statistics.mean(dt) for dt in all_parts_per_dt]
    quality_good_parts = [statistics.mean([x for x in dt if x >= min_acceptable_quality])
                          for dt in all_parts_per_dt]
    # Plot the data.
    figure, (g1, g2) = pyplot.subplots(1, 2, figsize = (12, 6))
    figure.canvas.manager.set_window_title('Close window to continue.')
    g1.set(xlabel = 'damage threshold to request maintenance',
           ylabel = 'parts produced',
           title = 'Produced Parts')
    g1.plot(thresholds, all_parts_counts, lw = 1, color = 'b', marker = '.',
            label = f'all parts')
    g1.plot(thresholds, good_parts_counts, lw = 3, color = 'g', marker = 'o',
            label = f'quality >= {min_acceptable_quality}')
    g1.plot(thresholds, bad_parts_counts, lw = 1, color = 'r', marker = '.',
            label = f'quality < {min_acceptable_quality}')
    g1.legend()
    g2.set(xlabel = 'damage threshold to request maintenance',
           ylabel = f'mean part quality',
           title = 'Part Quality')
    g2.plot(thresholds, quality_all_parts, lw = 1, color = 'b', marker = '.',
            label = 'all parts')
    g2.plot(thresholds, quality_good_parts, lw = 3, color = 'g', marker = 'o',
            label = f'quality >= {min_acceptable_quality}')
    g2.legend()

    if not is_test:
        print('Showing graphs in a separate window.')
        pyplot.show()
    else:
        print('Simulation finished.')


def generate_machine(name, upstream, maintainer):
    ''' Create and configure a part processing machine for this
    experiment.
    '''
    new_machine = MachineWithDamage(
            name = name,
            upstream = upstream,
            cycle_time = cycle_time,
            period_to_degrade = d_period,
            probability_to_degrade = d_probability,
            damage_on_degrade = d_magnitude,
            damage_to_fail = d_fail,
            get_maintenance_duration = lambda d, t: time_to_repair,
            get_capacity_to_maintain = lambda d, t: capacity_to_repair
    )

    def finish_processing(machine, part):
        # Part quality is adjusted based on current machine's damage level.
        damage = machine.damage
        # Damage negatively affects part quality. The relationship is
        # exponential. Gauss distribution is used for noise.
        part.quality = max(0, 1 - max(0, random.gauss(pow(damage, 3) * 0.01, .1)))

    def on_status_degrade(machine):
        # Request maintenance if damage is above threshold.
        if machine.damage >= damage_threshold:
            maintainer.create_work_order(new_machine)

    new_machine.add_finish_processing_callback(finish_processing)
    new_machine.add_on_degrade_callback(on_status_degrade)
    return new_machine


if __name__ == '__main__':
    main(len(sys.argv) > 1 and sys.argv[1] == 'testing')
