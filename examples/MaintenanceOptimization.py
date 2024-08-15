'''Example for quantifying the impact of different
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
from simprocesd.model.factory_floor import Source, Sink, Maintainer

from machine_with_damage import MachineWithDamage

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


def simulation(system, index, damage_threshold):
    # Setup the experiment.
    maintainer = Maintainer(capacity = maintainer_capacity)
    source = Source('Source', cycle_time = 1)
    M1 = CustomMachineWithDamage('M1', [source], maintainer, damage_threshold)
    M2 = CustomMachineWithDamage('M2', [source], maintainer, damage_threshold)
    M3 = CustomMachineWithDamage('M3', [source], maintainer, damage_threshold)
    M4 = CustomMachineWithDamage('M4', [source], maintainer, damage_threshold)
    M5 = CustomMachineWithDamage('M5', [source], maintainer, damage_threshold)
    all_machines = [M1, M2, M3, M4, M5]
    sink = Sink('Sink', all_machines, collect_parts = True)

    system.simulate(simulation_duration = simulation_duration, print_summary = False)


def main(is_test = False):
    global iterations
    if is_test:
        # Reduce example runtime during testing.
        iterations = 1

    print('Running simulations...')
    all_parts_per_dt = []
    # Damage thresholds go from d_magnitude to d_fail in increments
    # of  d_magnitude.
    thresholds = [x * d_magnitude for x in range(1, round(d_fail / d_magnitude) + 1)]
    tested_policies_count = len(thresholds)

    # Loop for collecting data on each maintenance policy.
    for current_threshold in thresholds:
        damage_threshold = current_threshold
        systems = System.simulate_multiple_times(simulation = simulation,
                                                 number_of_simulations = iterations,
                                                 max_processes = 4,
                                                 damage_threshold = damage_threshold)
        all_parts_per_dt.append([])
        # Collect completed Parts quality from each iteration.
        for s in systems:
            sink = s.find_assets(name = 'Sink')[0]
            all_parts_per_dt[-1] += ([x.quality for x in sink.collected_parts])

    # Get means for each maintenance policy.
    mean_part_count_per_dt = [len(dt) / iterations for dt in all_parts_per_dt]
    mean_good_part_count_per_dt = [len([x for x in dt if x >= min_acceptable_quality]) / iterations
                                   for dt in all_parts_per_dt]
    mean_bad_part_count_per_dt = [mean_part_count_per_dt[i] - mean_good_part_count_per_dt[i]
                                  for i in range(tested_policies_count)]
    mean_quality_per_dt = [statistics.mean(dt) for dt in all_parts_per_dt]
    mean_quality_good_parts_per_dt = [statistics.mean([x for x in dt if x >= min_acceptable_quality])
                                      for dt in all_parts_per_dt]

    # Plot the data.
    figure, (g1, g2) = pyplot.subplots(1, 2, figsize = (12, 6))
    figure.canvas.manager.set_window_title('Close window to continue.')
    g1.set(xlabel = 'damage threshold to request maintenance',
           ylabel = 'parts produced',
           title = 'Produced Parts')
    g1.plot(thresholds, mean_part_count_per_dt, lw = 1, color = 'b', marker = '.',
            label = f'all parts')
    g1.plot(thresholds, mean_good_part_count_per_dt, lw = 3, color = 'g', marker = 'o',
            label = f'quality >= {min_acceptable_quality}')
    g1.plot(thresholds, mean_bad_part_count_per_dt, lw = 1, color = 'r', marker = '.',
            label = f'quality < {min_acceptable_quality}')
    g1.legend()
    g2.set(xlabel = 'damage threshold to request maintenance',
           ylabel = f'mean part quality',
           title = 'Part Quality')
    g2.plot(thresholds, mean_quality_per_dt, lw = 1, color = 'b', marker = '.',
            label = 'all parts')
    g2.plot(thresholds, mean_quality_good_parts_per_dt, lw = 3, color = 'g', marker = 'o',
            label = f'quality >= {min_acceptable_quality}')
    g2.legend()

    if not is_test:
        print('Showing graphs in a separate window.')
        pyplot.show()
    else:
        print('Simulation finished.')


class CustomMachineWithDamage(MachineWithDamage):

    def __init__(self, name, upstream, maintainer, maintenance_threshhold):
        super().__init__(name = name,
                         upstream = upstream,
                         cycle_time = cycle_time,
                         period_to_degrade = d_period,
                         probability_to_degrade = d_probability,
                         damage_on_degrade = d_magnitude,
                         damage_to_fail = d_fail)
        self._maintainer = maintainer
        self._maintenance_threshhold = maintenance_threshhold

        self.add_finish_processing_callback(self._finish_processing)
        self.add_on_degrade_callback(self._on_status_degrade)

    def _finish_processing(self, machine, part):
        # Part quality is adjusted based on current machine's damage level.
        damage = machine.damage
        # Damage negatively affects part quality. The relationship is
        # exponential. Gauss distribution is used for noise.
        part.quality = max(0, 1 - max(0, random.gauss(pow(damage, 3) * 0.01, .1)))

    def _on_status_degrade(self, machine):
        # Request maintenance if damage is above threshold.
        if machine.damage >= self._maintenance_threshhold and self._maintainer != None:
            self._maintainer.create_work_order(machine)

    def get_work_order_duration(self, tag):
        return time_to_repair

    def get_work_order_capacity(self, tag):
        return capacity_to_repair


if __name__ == '__main__':
    main(len(sys.argv) > 1 and sys.argv[1] == 'testing')
