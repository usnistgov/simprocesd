'''Create a function that sets up and runs the model.
Use that function to run multiple simulations.
Collect data from each simulation and graph it.
'''
import random
import statistics
import sys
import time

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, PartProcessor, Sink
from simprocesd.utils.simulation_info_utils import simple_plot


# Part quality will be randomly distributed between 0 and 1
def process_part(processor, part):
    part.quality = random.random()


def simulation(system, index):
    # random.seed ensures that the results will be the same each time
    # the example is ran within the same Python environment no matter
    # how many processes are used to run the simulations.
    random.seed(index)
    source = Source(cycle_time = 1)
    M1 = PartProcessor('M1', upstream = [source], cycle_time = 1)

    M1.add_finish_processing_callback(process_part)
    sink = Sink(upstream = [M1])
    system.simulate(simulation_duration = 100, print_summary = False)


def main(is_test = False):
    simulation_count = 10
    start = time.time()
    # Run simulation function multiple times using up to 2 different
    # processes/CPU-cores.
    systems = System.simulate_multiple_times(simulation = simulation,
                                             number_of_simulations = simulation_count,
                                             max_processes = 2)
    duration = time.time() - start
    print(f'Simulation took {duration}')

    x = range(simulation_count)
    y = []
    for s in systems:
        # Retrieve produced part data for M1
        produced_part_data = s.simulation_data['produced_part']['M1']
        part_quality = statistics.mean([d[2] for d in produced_part_data])
        y.append(part_quality)

    if not is_test:
        print('Showing graph.')
        simple_plot(x = x, y = y, title = 'Mean part quality per iteration', xlabel = 'iteration',
                    ylabel = 'mean part quality')
    print('Done.')


if __name__ == '__main__':
    main(len(sys.argv) > 1 and sys.argv[1] == 'testing')
