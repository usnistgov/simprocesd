import random

from simprocesd.model.cms.cms import Cms
from simprocesd.model.factory_floor import Machine
from simprocesd.model.simulation import EventType
from simprocesd.utils import assert_callable


class MachineWithFaults(Machine):
    ''' A Machine that can be configured with a set of failure types
    where each failure is independent of the others and can be
    periodic or based on number of parts processed.
    See MachineWithFaults.add_recurring_fault()

    Arguments:
    name -- name of the machine.
    upstream -- list of upstream devices.
    cycle_time -- how long it takes to complete one process cycle.
    value -- starting value of the machine.
    '''

    def __init__(self,
                 name = None,
                 upstream = [],
                 cycle_time = 0,
                 value = 0):
        super().__init__(name, upstream, cycle_time, value)
        self._possible_faults = {}  # name, MachineFault
        self._active_faults = {}  # name, MachineFault

    @property
    def active_faults(self):
        return self._active_faults

    def initialize(self, env):
        super().initialize(env)

        for n, f in self._possible_faults.items():
            f.initialize(self)
            self._prepare_fault(f)

    def _on_received_new_part(self):
        super()._on_received_new_part()
        # Fault callbacks.
        for n, f in self._active_faults.items():
            if f.receive_part_callback != None:
                f.receive_part_callback(self._part)

        # Check if any faults need to cause machine to fail
        for n, f in self._possible_faults.items():
            if f.operations_to_fault != None:
                f.operations_since_last_fix += 1
                if f.operations_since_last_fix >= f.operations_to_fault:
                    # Reset operations to avoid scheduling multiple machine
                    # failures for same fault.
                    f.operations_to_fault = None
                    self._env.schedule_event(self._env.now,
                                             self.id,
                                             lambda: self._scheduled_fault(f),
                                             EventType.FAIL,
                                             f'Cycle count fault: {n}')

    def add_recurring_fault(self,
                 name = None,
                 get_time_to_fault = None,
                 get_operations_to_fault = None,  # start of n-th operation will trigger fault
                 get_time_to_maintain = lambda: 0,
                 get_cost_to_fix = lambda: 0,
                 get_false_alert_cost = lambda: 0,
                 is_hard_fault = True,  # will machine keep operating when fault occurs
                 capacity_to_repair = 1,
                 receive_part_callback = None,
                 failed_callback = None):
        '''
        Do not call after simulation starts.
        Arguments:
        name -- name of fault, used as maintenance tag to fix fault.
        get_time_to_fault -- function that gives time to fault, no
            periodic faults if not set.
        get_operations_to_fault -- function that returns n and n-th
            operation will trigger the fault, n is infinite if not set.
        get_time_to_maintain -- how long it takes for maintenance to
            fix this fault.
        get_cost_to_fix -- how much it costs to fix this fault.
        get_false_alert_cost -- how much it costs to fix this fault.
        is_hard_fault -- will machine keep operating when fault occurs.
        capacity_to_repair -- maintainer capacity needed while
            maintaining this fault.
        receive_part_callback = called with received part if the fault
            occurred and has not been maintained yet.
        failed_callback -- called with machine, and fault name when
            this fault occurs.
        '''
        if name == None:
            name = f'Failure_{len(self._possible_faults)}'
        assert not name in self._possible_faults.keys(), \
            f'Failure with that name already exists: {name}'

        mf = RecurringMachineFault(name, get_time_to_fault,
            get_operations_to_fault, get_time_to_maintain, get_cost_to_fix,
            get_false_alert_cost, is_hard_fault, capacity_to_repair,
            receive_part_callback, failed_callback
        )
        self._possible_faults[name] = mf

    def _prepare_fault(self, fault):
        # If the fault is not scheduled then schedule or reschedule it to occur.
        if fault.scheduled_fault_time == None:
            if fault.remaining_time_to_fault != None:
                fault.scheduled_fault_time = self._env.now + fault.remaining_time_to_fault
                fault.remaining_time_to_fault = None
            elif fault.get_time_to_fault != None:
                fault.scheduled_fault_time = self._env.now + fault.get_time_to_fault()

            if fault.scheduled_fault_time != None:
                self._env.schedule_event(fault.scheduled_fault_time,
                                         self.id,
                                         lambda: self._scheduled_fault(fault),
                                         EventType.FAIL,
                                         f'Timed fault: {fault.name}')

        # Prepare operations based fault
        if (fault.get_operations_to_fault != None
                and fault.operations_to_fault == None):
            fault.operations_to_fault = fault.get_operations_to_fault()

    def _scheduled_fault(self, fault):
        self._active_faults[fault.name] = fault
        # Reset trackers because fault occurred
        fault.scheduled_fault_time = None
        fault.operations_to_fault = None
        fault.operations_since_last_fix = 0

        # Save time to fault if there are other faults waiting to happen.
        if fault.is_hard_fault:
            for n, f in self._active_faults.items():
                if fault != f and f.scheduled_fault_time != None:
                    f.remaining_time_to_fault = max(0, f.scheduled_fault_time - self._env.now)
                    f.scheduled_fault_time = None
            # Failing machine will cancel all currently scheduled events for the machine.
            self.schedule_failure(self._env.now,
                    f'Fault: {fault.name} on machine: {self.name}')

        if fault.failed_callback != None:
            fault.failed_callback(self, fault.name)

    # Beginning of Maintainable function overrides.
    def get_work_order_duration(self, fault_name):
        return self._possible_faults[fault_name].get_time_to_maintain()

    def get_work_order_capacity(self, fault_name):
        return self._possible_faults[fault_name].capacity_to_repair

    def get_work_order_cost(self, tag):
        return 0  # No additional cost to maintainer.

    def start_work(self, tag):
        self.shutdown()

    def end_work(self, fault_name):
        f = self._active_faults.get(fault_name)
        if f != None:
            del self._active_faults[fault_name]
            self.add_cost(f'fix-{fault_name}', f.get_cost_to_fix())
            self._prepare_fault(f)
        else:
            f = self._possible_faults[fault_name]
            self.add_cost(f'fix_false_alert-{fault_name}', f.get_false_alert_cost())

        self.restore_functionality()
    # End of Maintainable function overrides.


class RecurringMachineFault:

    def __init__(self,
                 name,
                 get_time_to_fault,
                 get_operations_to_fault,
                 get_time_to_maintain,
                 get_cost_to_fix,
                 get_false_alert_cost,
                 is_hard_fault,
                 capacity_to_repair,
                 receive_part_callback,
                 failed_callback
                 ):
        assert_callable(get_time_to_fault, True)
        assert_callable(get_operations_to_fault, True)
        assert_callable(get_time_to_maintain, False)
        assert_callable(get_cost_to_fix, False)
        assert_callable(get_false_alert_cost, False)
        assert_callable(receive_part_callback, True)
        assert_callable(failed_callback, True)

        self.name = name
        self.get_time_to_fault = get_time_to_fault
        self.get_operations_to_fault = get_operations_to_fault
        self.is_hard_fault = is_hard_fault
        self.get_time_to_maintain = get_time_to_maintain
        self.get_cost_to_fix = get_cost_to_fix
        self.get_false_alert_cost = get_false_alert_cost
        self.capacity_to_repair = capacity_to_repair
        self.receive_part_callback = receive_part_callback
        self.failed_callback = failed_callback

        self.scheduled_fault_time = None
        self.remaining_time_to_fault = None
        self.operations_since_last_fix = 0
        self.operations_to_fault = None

    @property
    def machine(self):
        return self._machine

    def initialize(self, machine):
        self._machine = machine
        self.scheduled_fault_time = None
        self.remaining_time_to_fault = None
        self.operations_since_last_fix = 0
        self.operations_to_fault = None


class CmsEmulator(Cms):
    ''' CMS emulator that is configured with average rates rather than
    actual detection logic. Built to work with MachineWithFaults.
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

    def on_sense(self, sensor, time, data):
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
                self.maintainer.create_work_order(self.machine[fault.name], fault.name)
        elif self.sense_fault_count[fault.name] == self.miss_count[fault.name]:
            # fault was missed earlier by CMS and is caught now by other means
            self.sense_fault_count[fault.name] = 0
            self.maintainer.create_work_order(self.machine[fault.name], fault.name)

    def check_for_false_alerts(self, allow_multiple = False):
        ''' Called when a sense event shows no ongoing faults so that false alerts can
        be triggered if any are supposed to happen.
        '''
        for name, count in self.fa_buffer.items():
            if count > 0 and random.random() < 0.01:
                self.fa_buffer[name] -= 1
                self.maintainer.create_work_order(self.machine[name], name)
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

