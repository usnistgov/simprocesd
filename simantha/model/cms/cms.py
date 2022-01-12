import random

from ..factory_floor.asset import Asset


class Cms(Asset):
    ''' Based class to represent a Condition Monitoring System.
    '''

    def __init__(self, maintainer, **kwargs):
        super().__init__(**kwargs)

        self.maintainer = maintainer
        self._sensors = []

    def initialize(self, env):
        super().initialize(env)
        self.maintainer.initialize(env)
        for s in self._sensors:
            s.initialize(env)

    def add_sensor(self, sensor):
        self._sensors.append(sensor)
        # user_data can be manipulated directly from sensor
        callback = lambda ud, d:self.on_sense(sensor, d)
        sensor.add_on_sense_callback(callback)

    def on_sense(self, sensor, data):
        pass


class CmsEmulator(Cms):
    ''' CMS emulator that is configured with average rates rather than actual
    detection logic.
    '''

    def __init__(self, maintainer, **kwargs):
        super().__init__(maintainer, **kwargs)

        self.machine = {}
        self.sense_fault_count = {}
        # How long until fault is detected if CMS catches or if it's missed.
        self.catch_count = {}
        self.miss_count = {}
        # False alert rates and missed alert rates.
        self.miss_rate = {}
        # False alert rate per real fault = fa_rate / (1 - fa_rate) assuming total rates of
        self.fa_rate = {}
        # How many false alerts are buffered.
        self.fa_buffer = {}

    def on_sense(self, sensor, data):
        raise NotImplementedError('on_sense needs to be implemented or'
                                  +' CustomCms will not do anything.')

    def on_soft_fault(self, fault):
        ''' Called when sensor detect an ongoing fault. Will increase sense_fault_count
        for this fault by one. If count reaches count_to_detection or
        on_miss_count_to_detection (based on miss_rate) a repair will be scheduled.
        '''
        self.sense_fault_count[fault.name] += 1
        if self.sense_fault_count[fault.name] == 1:
            # First bad part, fault just happened
            if random.random() < self.fa_rate[fault.name]:
                self.fa_buffer[fault.name] += 1
        elif self.sense_fault_count[fault.name] == self.catch_count[fault.name]:
            # reached count when a fault could be caught early
            if random.random() >= self.miss_rate[fault.name]:
                # fault is detected now
                self.sense_fault_count[fault.name] = 0
                self.maintainer.request_maintenance(self.machine[fault.name], fault.name)
        elif self.sense_fault_count[fault.name] == self.miss_count[fault.name]:
            # fault was missed earlier by CMS and is caught now by other means
            self.sense_fault_count[fault.name] = 0
            self.maintainer.request_maintenance(self.machine[fault.name], fault.name)

    def check_for_false_alerts(self, allow_multiple = False):
        ''' Called when a sense event shows no ongoing faults so that false alerts can
        be triggered if any are supposed to happen.
        '''
        for name, count in self.fa_buffer.items():
            if count > 0 and random.random() < 0.01:
                self.fa_buffer[name] -= 1
                self.maintainer.request_maintenance(self.machine[name], name)
                if not allow_multiple: return

    def configure_fault_handling(self, fault_name, machine,
                                   count_to_detection = 1,
                                   on_miss_count_to_detection = 2,
                                   miss_rate = 0,
                                   false_alert_rate = 0):
        assert miss_rate + false_alert_rate <= 1, \
            'miss_rate and false_alert_rate can not add up to more than one'
        self.machine[fault_name] = machine
        self.sense_fault_count[fault_name] = 0
        self.catch_count[fault_name] = count_to_detection
        self.miss_count[fault_name] = on_miss_count_to_detection
        self.miss_rate[fault_name] = miss_rate / (1 - false_alert_rate)
        self.fa_rate[fault_name] = false_alert_rate / (1 - false_alert_rate)
        self.fa_buffer[fault_name] = 0

