''' This example simulates a multistage manufacturing setup where the
machines accrue damage over time which negatively impacts the quality of
the parts those machines produce.
After the simulation finishes, the final part quality and the path that
each part took are used to determine problematic machines.
In perfect conditions each machine is expected to affect the part
quality equally.
'''
import random

import numpy
from scipy.optimize import minimize

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Buffer, Sink, Part, Maintainer
from simprocesd.utils import DataStorageType, geometric_distribution_sample, \
    print_produced_parts_and_average_quality

from .machine_with_damage import MachineWithDamage


def process_part(machine, part, quality_distribution):
    part.quality -= quality_distribution() * (machine.damage + random.uniform(-.01, .01))


def new_machine(name, upstream, cycle_time, probability_to_degrade,
                quality_distribution, maintainer):
    time_to_maintain = lambda m, d: geometric_distribution_sample(0.1, 1)
    machine = MachineWithDamage(name = name,
                                upstream = upstream,
                                cycle_time = cycle_time,
                                period_to_degrade = 1,
                                probability_to_degrade = probability_to_degrade,
                                damage_on_degrade = 1,
                                damage_to_fail = 5,
                                get_maintenance_duration = time_to_maintain,
                                get_capacity_to_maintain = lambda m, d: 1)
    machine.add_finish_processing_callback(lambda m, p: process_part(m, p, quality_distribution))
    machine.add_shutdown_callback(
            lambda m, is_failure, p: maintainer.create_work_order(m) if is_failure else None)
    return machine


def main():
    system = System(DataStorageType.MEMORY)

    maintainer = Maintainer(capacity = 1)
    source = Source('Source', Part('Part', 1, 2))
    M1 = new_machine('M1', [source], 1, 0.02, lambda: random.uniform(0, 0.01), maintainer)
    stage1 = [M1]
    B1 = Buffer('B1', stage1, capacity = 20)
    M2 = new_machine('M2', [B1], 1, 0.02, lambda: random.uniform(0, 0.01), maintainer)
    M3 = new_machine('M3', [B1], 1, 0.02, lambda: random.uniform(0, 0.02), maintainer)
    stage2 = [M2, M3]
    B2 = Buffer('B2', stage2, capacity = 10)
    M4 = new_machine('M4', [B2], 1, 0.02, lambda: random.uniform(0.01, 0.02), maintainer)
    M5 = new_machine('M5', [B2], 1, 0.05, lambda: random.uniform(0.025, 0.05), maintainer)
    stage3 = [M4, M5]
    B3 = Buffer('B3', stage3, capacity = 10)
    M6 = new_machine('M6', [B3], 1, 0.02, lambda: random.uniform(0, 0.02), maintainer)
    M7 = new_machine('M7', [B3], 1, 0.02, lambda: random.uniform(0.01, 0.02), maintainer)
    stage4 = [M6, M7]
    sink = Sink('Sink', stage4, collect_parts = True)

    random.seed(3)  # Setting seed ensures same results every run.
    system.simulate(simulation_duration = 2000)

    unique_machines = stage1 + stage2 + stage3 + stage4
    unique_machines.sort(key = lambda a: a.name)

    print_produced_parts_and_average_quality(system, unique_machines)

    unique_machine_names = [m.name for m in unique_machines]
    print('\nUnique machine names:')
    print(f'  {unique_machine_names}')

    # Path quality analysis, get unique paths.
    collected_part_data = []
    unique_paths = []
    for part in sink.collected_parts:
        routing_path = [m.name for m in part.routing_history if m.name in unique_machine_names]
        if routing_path not in unique_paths:
            unique_paths.append(routing_path)
        path_index = unique_paths.index(routing_path)
        collected_part_data.append((path_index, part.quality))
    print('Unique paths:')
    print(f'  {unique_paths}')

    # Represent paths as flags that represent machines.
    paths_map = []
    for up in unique_paths:
        p = [0] * len(unique_machines)
        for machine_name in up:
            p[unique_machine_names.index(machine_name)] = 1
        paths_map.append(p)
    print('Unique paths as flags in list:')
    print(f'  {paths_map}')

    # Calculate path quality.
    part_qualities_in_paths = [[] for i in range(len(unique_paths))]
    for path_index, quality in collected_part_data:
        part_qualities_in_paths[path_index].append(quality)
    path_quality = [sum(pq) / len(pq) for pq in part_qualities_in_paths]
    print('Path quality:')
    print(f'  {path_quality}')

    error = lambda b: numpy.sum(numpy.abs(numpy.dot(paths_map, b) - path_quality))
    lb = -1
    ub = 1
    bnds = [(lb, ub) for i in range(len(unique_machines))]
    res = minimize(error, x0 = [1] * len(unique_machines), bounds = bnds,
                   options = {'ftol':1e-7, 'gtol':1e-7})
    print('Predicted machine\'s part quality impact [M1-M7]:')
    predicted_part_quality_impact = str(res.x).replace('\n', '')  # Remove newlines
    print(f'  {predicted_part_quality_impact}')
    machine_at_fault = unique_machine_names[numpy.argmin(res.x)]
    print(f'Machine with lowest part quality impact: {machine_at_fault}')


if __name__ == '__main__':
    main()
