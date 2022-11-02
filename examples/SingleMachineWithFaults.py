'''
An example of Markovian degradation of a single machine. Once the
machine reaches the zero health it will shut down and stop receiving
and processing parts until maintained. Machine degradation is simulated
by a periodic fault.
Expected parts produced: about 8000
'''

import random

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Sink, Maintainer
from simprocesd.utils import geometric_distribution_sample

from .machine_with_faults import MachineWithFaults


def main():
    system = System()
    maintainer = Maintainer()

    source = Source()
    M1 = MachineWithFaults('M1', cycle_time = 1, upstream = [source])
    M1.add_recurring_fault('Fault',
        get_time_to_fault = lambda: geometric_distribution_sample(0.1, 4),
        get_time_to_maintain = lambda: geometric_distribution_sample(0.1, 1))

    on_shutdown_cb = lambda m, is_failure, p: maintainer.create_work_order(m, 'Fault')
    M1.add_shutdown_callback(on_shutdown_cb)
    sink = Sink(upstream = [M1])

    random.seed(1)
    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_duration = 60 * 24 * 7)


if __name__ == '__main__':
    main()
