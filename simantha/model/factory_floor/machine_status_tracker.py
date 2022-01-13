from ...utils import assert_callable
from ..simulation import EventType


class MachineStatusTracker:

    def __init__(self):
        self._receive_part_callbacks = []
        self._finish_processing_callbacks = []
        self._failed_callbacks = []
        self._restored_callbacks = []
        self._machine = None
        self._env = None
        self._possible_faults = {}  # name, MachineFault
        self._active_faults = {}  # name, MachineFault

    @property
    def machine(self):
        return self._machine

    @property
    def possible_faults(self):
        return self._possible_faults

    @property
    def active_faults(self):
        return self._active_faults

    def initialize(self, machine, env):
        self._machine = machine
        self._env = env

        for n, f in self._possible_faults.items():
            f.initialize(self)
            self._prepare_fault(f)

    def add_receive_part_callback(self, callback):
        assert_callable(callback)
        self._receive_part_callbacks.append(callback)

    def add_finish_processing_callback(self, callback):
        assert_callable(callback)
        self._finish_processing_callbacks.append(callback)

    def add_failed_callback(self, callback):
        assert_callable(callback)
        self._failed_callbacks.append(callback)

    def add_restored_callback(self, callback):
        assert_callable(callback)
        self._restored_callbacks.append(callback)

    def receive_part(self, part):
        for c in self._receive_part_callbacks:
            c(part)

        # Check if any faults need to cause machine to fail
        for n, f in self._possible_faults.items():
            if f.operations_to_fault != None:
                f.operations_since_last_fix += 1
                if f.operations_since_last_fix >= f.operations_to_fault:
                    # Reset operations to avoid scheduling multiple machine
                    # failures for same fault.
                    f.operations_to_fault = None
                    self._env.schedule_event(self._env.now,
                                             self._machine.id,
                                             lambda: self._scheduled_fault(f),
                                             EventType.FAIL,
                                             f'Cycle count fault: {n}')

    def finish_processing(self, part):
        # Fault callbacks.
        for n, f in self._active_faults.items():
            if f.finish_processing_callback != None:
                f.finish_processing_callback(part)
        # Other callbacks.
        for c in self._finish_processing_callbacks:
            c(part)

    def failed(self):
        for c in self._failed_callbacks:
            c()

    def fix_fault(self, fault_name):
        assert fault_name != None, 'fault_name can not be None'

        f = self._active_faults.get(fault_name)
        if f != None:
            del self._active_faults[fault_name]
            self._machine.add_cost(f'fix-{fault_name}', f.get_cost_to_fix())
            self._prepare_fault(f)
        else:
            f = self._possible_faults[fault_name]
            self._machine.add_cost(f'fix_false_alert-{fault_name}', f.get_false_alert_cost())

    def restored(self, fault_name):
        for c in self._restored_callbacks:
            c(fault_name)

    def add_recurring_fault(self,
                 name = None,
                 get_time_to_fault = None,
                 get_operations_to_fault = None,  # start of n-th operation will trigger fault
                 get_time_to_repair = lambda: 0,
                 get_cost_to_fix = lambda: 0,
                 get_false_alert_cost = lambda: 0,
                 is_hard_fault = True,  # will machine keep operating when fault occurs
                 capacity_to_repair = 1,
                 finish_processing_callback = None,
                 failed_callback = None):
        if name == None:
            name = f'Failure_{len(self._possible_faults)}'
        assert not name in self._possible_faults.keys(), \
            f'Failure with that name already exists: {name}'

        mf = MachineFault(name, get_time_to_fault,
                          get_operations_to_fault, get_time_to_repair, get_cost_to_fix,
                          get_false_alert_cost, is_hard_fault, capacity_to_repair,
                          finish_processing_callback, failed_callback)
        self._possible_faults[name] = mf

    def has_active_hard_faults(self):
        for n, f in self._active_faults.items():
            if f.is_hard_fault:
                return True
        return False

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
                                         self._machine.id,
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
                    f.remaining_time_to_fault = max(0,
                          f.scheduled_fault_time - self._env.now)
                    f.scheduled_fault_time = None
            # Failing machine will cancel all currently scheduled events for the machine.
            self._machine.fail()

        if fault.failed_callback != None:
            fault.failed_callback(fault)


class MachineFault:

    def __init__(self,
                 name,
                 get_time_to_fault,
                 get_operations_to_fault,
                 get_time_to_repair,
                 get_cost_to_fix,
                 get_false_alert_cost,
                 is_hard_fault,
                 capacity_to_repair,
                 finish_processing_callback,
                 failed_callback
                 ):
        assert_callable(get_time_to_fault, True)
        assert_callable(get_operations_to_fault, True)
        assert_callable(get_time_to_repair, False)
        assert_callable(get_cost_to_fix, False)
        assert_callable(get_false_alert_cost, False)
        assert_callable(finish_processing_callback, True)
        assert_callable(failed_callback, True)

        self.name = name
        self.get_time_to_fault = get_time_to_fault
        self.get_operations_to_fault = get_operations_to_fault
        self.is_hard_fault = is_hard_fault
        self.get_time_to_repair = get_time_to_repair
        self.get_cost_to_fix = get_cost_to_fix
        self.get_false_alert_cost = get_false_alert_cost
        self.capacity_to_repair = capacity_to_repair
        self.finish_processing_callback = finish_processing_callback
        self.failed_callback = failed_callback

        self.scheduled_fault_time = None
        self.remaining_time_to_fault = None
        self.operations_since_last_fix = 0
        self.operations_to_fault = None

    @property
    def machine(self):
        return self._machine_status.machine

    def initialize(self, machine_status):
        self._machine_status = machine_status
