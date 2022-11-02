''' Time units are seconds and value is in dollars.
Machine produces 10 items per second but we will have each Part
represent 50 items in order to speed up the simulation.
Expected parts produced: 75005
Expected yearly operational profit of using a CMS is: about $130,000
'''

import random
import sys

from simprocesd.model import System
from simprocesd.model.factory_floor import Source, Sink, Part, Maintainer
from simprocesd.model.sensors import OutputPartSensor, AttributeProbe, Probe

from .machine_with_faults import MachineWithFaults, CmsEmulator

count_per_part = 50  # set to 1 for more accurate results
processing_rate = 10
machine_cycle_time = count_per_part / processing_rate
# Machine operates an average of 4.1667 hours per day
operating_time_per_day = 60 * 60 * 4.1667
dulling_name = 'Dulling'
ma_name = 'Misalignment'


def main(is_test = False):
    # Working year; 5 days a week and 50 weeks a year.
    duration = operating_time_per_day * 5 * 50
    if is_test:
        # Reduce example runtime for test.
        duration /= 100

    random.seed(1)

    no_cms_net = sample(duration, False)
    print(f'Net value without CMS: ${no_cms_net}')
    with_cms_net = sample(duration, True)
    print(f'Net value with CMS: ${with_cms_net}')
    print(f'Yearly operational profit of using a CMS is: ${with_cms_net - no_cms_net}')


class CustomCms(CmsEmulator):

    def on_sense(self, sensor, time, data):
        ''' data[0] is p1 data: part quality
        data[1] is p2 data: dictionary of machine's active faults indexed by fault name
        '''
        # example on how to differentiate between multiple sensors
        if sensor.name != 'M1 Sensor': return

        if data[0] < 1:  # Part quality is low, check for faults
            for name, fault in data[1].items():
                self.on_soft_fault(fault)
        else:  # No active fault
            self.check_for_false_alerts()


def sample(duration, with_cms):
    system = System()

    part = Part(value = 0, quality = 1)
    source = Source(sample_part = part)

    M1 = MachineWithFaults('M1', upstream = [source], cycle_time = machine_cycle_time)
    M1.add_finish_processing_callback(default_part_processing)
    M1.add_recurring_fault(
        name = dulling_name,
        # Failure rate of once in 100 days.
        get_time_to_fault = lambda: distributed_ttf(100),
        get_cost_to_fix = lambda: 100,
        get_false_alert_cost = lambda: 85,
        is_hard_fault = False,
        receive_part_callback = wasted_part_processing
    )
    M1.add_recurring_fault(
        name = ma_name,
        # Failure rate of ~99% per day.
        get_time_to_fault = lambda: distributed_ttf(1.01),
        get_cost_to_fix = lambda: 75,
        get_false_alert_cost = lambda: 85,
        is_hard_fault = False,
        receive_part_callback = wasted_part_processing
    )

    sink = Sink(upstream = [M1])

    maintainer = Maintainer()
    cms = CustomCms(maintainer, name = "CMS")
    cms.configure_fault_handling(dulling_name, M1,
                                   100 / count_per_part,
                                   300 / count_per_part,
                                   0.01 if with_cms else 1,
                                   0.05 if with_cms else 0)
    cms.configure_fault_handling(ma_name, M1,
                                   150 / count_per_part,
                                   500 / count_per_part,
                                   0.001 if with_cms else 1,
                                   0.01 if with_cms else 0)

    # Probe target will be overwritten by OutputPartSensor
    p1 = AttributeProbe('quality', None)
    p2 = Probe(lambda t: M1.active_faults, None)
    sensor = OutputPartSensor(M1, [p1, p2], name = 'M1 Sensor')
    cms.add_sensor(sensor)

    system.simulate(duration)
    return system.get_net_value_of_assets()


def distributed_ttf(days_to_fault):
    ttf = days_to_fault * operating_time_per_day
    return random.normalvariate(ttf, ttf * 0.05)


def wasted_part_processing(part):
    part.quality = 0
    part.add_cost('M1_failed_processing', part.value)


def default_part_processing(machine, part):
    if part.quality > 0:
        part.add_value('M1_processing', 1.5 * count_per_part * part.quality)


if __name__ == '__main__':
    main(len(sys.argv) > 1 and sys.argv[1] == 'testing')
