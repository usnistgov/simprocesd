'''
An example of Markovian degradation of a single machine. Once the
machine reaches the zero health it will shut down and stop receiving
and processing parts until maintained. Machine degradation is simulated
by a periodic fault.
Expected parts produced: about 8000
'''

import random

from ..model import System
from ..model.factory_floor import Source, Machine, Sink, Maintainer
from ..utils import geometric_distribution_sample
from .status_tracker_with_faults import StatusTrackerWithFaults


def main():
    maintainer = Maintainer()
    source = Source()
    M1 = Machine('M1',
                 cycle_time = 1,
                 upstream = [source],
                 status_tracker = StatusTrackerWithFaults())
    M1.status_tracker.add_recurring_fault('Fault',
        get_time_to_fault = lambda: geometric_distribution_sample(0.1, 4),
        get_time_to_maintain = lambda: geometric_distribution_sample(0.1, 1))
    M1.add_failed_callback(lambda p: maintainer.request_maintenance(M1, 'Fault'))
    sink = Sink(upstream = [M1])

    system = System([source, M1, sink, maintainer])

    random.seed(1)
    # If time units are minutes then simulation period is a week.
    system.simulate(simulation_time = 60 * 24 * 7)


if __name__ == '__main__':
    main()
