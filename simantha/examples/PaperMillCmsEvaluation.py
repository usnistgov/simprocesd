import random

from .. import Source, Machine, Sink, System, Part
from ..components.machine_status import MachineStatus
from ..components.sensor import OutputPartSensor, AttributeProbe, Probe
from ..components.cms import CmsEmulator
from ..maintainer import Maintainer

''' Time units are seconds and value is in dollars.
Machine produces 10 items per second but we will have each Part represent 50 items in
order to speed up the simulation.
'''
count_per_part = 50
processing_rate = 10
machine_cycle_time = count_per_part / processing_rate
# Machine operates an average of 4.1667 hours per day
operating_time_per_day = 60 * 60 * 4.1667
dulling_name = 'Dulling'
ma_name = 'Misalignment'


def main():
    random.seed(1)
    # Working year; 5 days a week and 50 weeks a year.
    duration = operating_time_per_day * 5 * 50

    no_cms_net = sample(duration, False)
    print(f'Net value without CMS: ${no_cms_net}')
    with_cms_net = sample(duration, True)
    print(f'Net value with CMS: ${with_cms_net}')
    print(f'Yearly operational profit of using a CMS is: ${with_cms_net - no_cms_net}')


class CustomCms(CmsEmulator):

    def on_sense(self, sensor, data):
        ''' data[0] is p1 data: part quality
        data[1] is p2 data: dictionary of machine's active failures indexed by failure name
        '''
        # example on how to differentiate between multiple sensors
        if sensor.name != 'M1 Sensor': return

        if data[0] < 1:  # Part quality is low, check for faults
            for name, failure in data[1].items():
                self.on_soft_failure(failure)
        else:  # No active failure
            self.check_for_false_alerts()


def sample(duration, with_cms):
    part = Part(f'{count_per_part}xPart', 0, 1)

    status = MachineStatus()
    status.add_finish_processing_callback(default_part_processing)
    status.add_failure(name = dulling_name,
                        # Failure rate of 100 days.
                        get_time_to_failure = lambda: distributed_ttf(100),
                        get_cost_to_fix = lambda: 100,
                        get_false_alert_cost = lambda: 85,
                        is_hard_failure = False,
                        finish_processing_callback = wasted_part_processing)
    status.add_failure(name = ma_name,
                        # Failure rate 99% per day.
                        get_time_to_failure = lambda: distributed_ttf(1.01),
                        get_cost_to_fix = lambda: 75,
                        get_false_alert_cost = lambda: 85,
                        is_hard_failure = False,
                        finish_processing_callback = wasted_part_processing)

    source = Source(sample_part = part)
    M1 = Machine('M1', upstream = [source], machine_status = status,
                 cycle_time = machine_cycle_time)
    sink = Sink(upstream = [M1])

    maintainer = Maintainer()
    cms = CustomCms(maintainer, name = "CMS")
    cms.configure_failure_handling(dulling_name, M1,
                                   100 / count_per_part,
                                   300 / count_per_part,
                                   0.01 if with_cms else 1,
                                   0.05 if with_cms else 0)
    cms.configure_failure_handling(ma_name, M1,
                                   150 / count_per_part,
                                   500 / count_per_part,
                                   0.001 if with_cms else 1,
                                   0.01 if with_cms else 0)

    # target will be overwritten by OutputPartSensor
    p1 = AttributeProbe('quality', None)
    p2 = Probe(lambda t: M1.machine_status.active_failures, None)
    sensor = OutputPartSensor(M1, [p1, p2], name = 'M1 Sensor')
    cms.add_sensor(sensor)

    system = System([source, M1, sink, cms])

    system.simulate(duration)
    return system.get_net_value()


def distributed_ttf(days_to_failure):
    ttf = days_to_failure * operating_time_per_day
    return random.normalvariate(ttf, ttf * 0.05)


def wasted_part_processing(part):
    part.value = 0
    part.quality = 0


def default_part_processing(part):
    part.value = 1.5 * count_per_part * part.quality


if __name__ == '__main__':
    main()
