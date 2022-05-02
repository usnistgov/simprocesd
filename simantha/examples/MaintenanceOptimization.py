'''
Example for quantifying the impact of different
Condition Based Maintenance (CBM) policies.

Setup: there are 5 machines in parallel that accrue damage over time
which negatively affects the part quality (0-1). Only parts of quality
min_acceptable_quality and higher are considered good/acceptable.
'''
import random
import statistics
from matplotlib import pyplot

from ..model import System
from ..model.factory_floor import Source, Machine, Sink, Maintainer, Part
from ..utils import DataStorageType
from .status_tracker_with_damage import StatusTrackerWithDamage

# Setup parameters
capacity_to_repair = 1
maintainer_capacity = 2
time_to_repair = 150
cycle_time = 5
min_acceptable_quality = 0.9
# Machine damage parameters.
d_period, d_probability, d_magnitude, d_fail = 60, 0.33, .5, 5
# Simulation time per iteration. 1 week (12 operational hours a day).
simulation_time = 60 * 12 * 7
# Iterations per threshold.
iterations = 10


def main():
    random.seed(1)
    # Damage thresholds to test and plot.
    thresholds = [x * d_magnitude for x in range(1, round((d_fail / d_magnitude)) + 1)]
    print(f'Simulating {len(thresholds)} configuartion/s: ', end = '')
    results = []
    for damage_threshold in thresholds:
        print('.', end = '')
        results.append([])
        for i in range(iterations):
            results[-1].append(run_experiment(damage_threshold))
    print('\n')

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
    pyplot.show()


def generate_machine(name, upstream, damage_threshold, maintainer):
    ''' Create and configure a part processing machine for this
    experiment.
    '''
    st = StatusTrackerWithDamage(d_period, d_probability, d_magnitude, d_fail,
                                 get_time_to_maintain = lambda damage: time_to_repair,
                                 get_capacity_to_maintain = lambda damage: capacity_to_repair)
    new_machine = Machine(name, upstream, cycle_time, st)

    def finish_processing(part):
        # Part quality is adjusted based on current machine's damage level.
        damage = new_machine.status_tracker.damage
        # Damage negatively affects part quality. The relationship is
        # exponential. Gauss distribution is used for noise.
        part.quality = max(0, 1 - max(0, random.gauss(pow(damage, 3) * 0.01, .1)))

    def on_status_degrade(damage):
        # Request maintenance if damage is above threshold.
        if damage >= damage_threshold:
            maintainer.request_maintenance(new_machine)

    new_machine.add_finish_processing_callback(finish_processing)
    st.add_on_degrade_callback(on_status_degrade)
    return new_machine


def run_experiment(damage_threshold):
    ''' Returns a list of every produced part's quality in the Sink.
    '''
    maintainer = Maintainer(capacity = maintainer_capacity)

    source = Source('Source', Part(quality = 1), 1)
    M1 = generate_machine('M1', [source], damage_threshold, maintainer)
    M2 = generate_machine('M2', [source], damage_threshold, maintainer)
    M3 = generate_machine('M3', [source], damage_threshold, maintainer)
    M4 = generate_machine('M4', [source], damage_threshold, maintainer)
    M5 = generate_machine('M5', [source], damage_threshold, maintainer)
    all_machines = [M1, M2, M3, M4, M5]
    sink = Sink('Sink', all_machines, collect_parts = True)

    system = System(all_machines + [source, sink, maintainer], DataStorageType.MEMORY)
    system.simulate(simulation_time = simulation_time, print_summary = False)

    return [x.quality for x in sink.collected_parts]


if __name__ == '__main__':
    main()
