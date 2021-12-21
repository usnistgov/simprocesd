import random

from .. import Source, Machine, Sink, System, Part
from ..components.machine_status import MachineStatus
from ..components.sensor import OutputPartSensor, AttributeProbe, Probe
from ..components.cms import CMS
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


class CustomCMS(CMS):

    def __init__(self, maintainer, machine, with_cms, **kwargs):
        super().__init__(maintainer, **kwargs)
        self.machine = machine
        self.part_count = {dulling_name: 0, ma_name: 0}
        # How long until fault is detected if CMS catches or if it's missed.
        self.miss_count = {dulling_name: 300 / count_per_part,
                                ma_name: 500 / count_per_part}
        self.catch_count = {dulling_name: 100 / count_per_part,
                                ma_name: 150 / count_per_part}
        # False alert rates and missed alert rates.
        self.miss_rate = {dulling_name: 0.01 if with_cms else 1,
                          ma_name: 0.001 if with_cms else 1}
        # False alert rate per real failure = fa_rate / (1 - fa_rate) assuming total rates of
        self.fa_rate = {dulling_name: 0.05 if with_cms else 0,
                        ma_name: 0.01 if with_cms else 0}
        # How many false alerts are buffered.
        self.fa_buffer = {dulling_name: 0, ma_name: 0}

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
            self.check_for_false_alert()

    def on_soft_failure(self, failure):
        self.part_count[failure.name] += 1
        if self.part_count[failure.name] == 1:
            # First bad part, failure just happened
            if random.random() < self.fa_rate[failure.name]:
                self.fa_buffer[failure.name] += 1
        elif self.part_count[failure.name] == self.catch_count[failure.name]:
            # reached count when a failure could be caught early
            if random.random() >= self.miss_rate[failure.name]:
                print(f'caught failure repair: {failure.name}')
                # failure is detected now
                self.part_count[failure.name] = 0
                self.maintainer.request_maintenance(self.machine, failure.name)
        elif self.part_count[failure.name] == self.miss_count[failure.name]:
            print(f'missed failure repair: {failure.name}')
            # failure was missed earlier by CMS and is caught now by other means
            self.part_count[failure.name] = 0
            self.maintainer.request_maintenance(self.machine, failure.name)

    def check_for_false_alert(self):
        for name, count in self.fa_buffer.items():
            if count > 0 and random.random() < 0.01:
                print(f'false alert for: {name}')
                self.fa_buffer[name] -= 1
                self.maintainer.request_maintenance(self.machine, name)


def sample(duration, with_cms):
    part = Part(f'{count_per_part}xPart', 0, 1)

    status = MachineStatus()
    status.add_finish_processing_callback(default_part_processing)
    status.add_failure(name = dulling_name,
                        # Failure rate of 100 days.
                        get_time_to_failure = lambda: 100 * operating_time_per_day,
                        get_cost_to_fix = lambda: 100,
                        get_false_alert_cost = lambda: 85,
                        is_hard_failure = False,
                        finish_processing_callback = wasted_part_processing)
    status.add_failure(name = ma_name,
                        # Failure rate 99% per day.
                        get_time_to_failure = lambda: 1.01 * operating_time_per_day,
                        get_cost_to_fix = lambda: 75,
                        get_false_alert_cost = lambda: 85,
                        is_hard_failure = False,
                        finish_processing_callback = wasted_part_processing)

    source = Source(sample_part = part)
    M1 = Machine('M1', upstream = [source], machine_status = status,
                 cycle_time = machine_cycle_time)
    sink = Sink(upstream = [M1])

    maintainer = Maintainer()
    cms = CustomCMS(maintainer, M1, with_cms, name = "default")
    # target will be overwritten by OutputPartSensor
    p1 = AttributeProbe('quality', None)
    p2 = Probe(lambda t: M1.machine_status.active_failures, None)
    sensor = OutputPartSensor(M1, [p1, p2], name = 'M1 Sensor')
    cms.add_sensor(sensor)

    system = System([source, M1, sink, cms])

    system.simulate(duration)
    return system.get_net_value()


def wasted_part_processing(part):
    part.value = 0
    part.quality = 0


def default_part_processing(part):
    part.value = 1.5 * count_per_part * part.quality


if __name__ == '__main__':
    main()
