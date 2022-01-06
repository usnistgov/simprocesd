from ..utils import assert_callable
from ..simulation import EventType


class MachineStatus:

    def __init__(self):
        self._receive_part_callbacks = []
        self._finish_processing_callbacks = []
        self._failed_callbacks = []
        self._restored_callbacks = []
        self._machine = None
        self._env = None
        self._possible_failures = {}  # name, MachineFailure
        self._active_failures = {}  # name, MachineFailure

    @property
    def machine(self):
        return self._machine

    @property
    def possible_failures(self):
        return self._possible_failures

    @property
    def active_failures(self):
        return self._active_failures

    def initialize(self, machine, env):
        self._machine = machine
        self._env = env

        for n, f in self._possible_failures.items():
            f.initialize(self)
            self._prepare_next_failures(f)

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

        # Check if any failures are happening
        for n, f in self._possible_failures.items():
            if f.operations_to_failure != None:
                f.operations_since_last_fix += 1
                if f.operations_since_last_fix >= f.operations_to_failure:
                    # Reset operations to avoid scheduling multiple fails for same failure
                    f.operations_to_failure = None
                    self._env.schedule_event(self._env.now,
                                             self._machine.id,
                                             lambda: self._scheduled_fail(f),
                                             EventType.FAIL,
                                             f'Cycle count failure: {n}')

    def finish_processing(self, part):
        for n, f in self._active_failures.items():
            if f.finish_processing_callback != None:
                f.finish_processing_callback(part)

        for c in self._finish_processing_callbacks:
            c(part)

    def failed(self):
        for c in self._failed_callbacks:
            c()

    def fix_failure(self, failure_name):
        assert failure_name != None, 'failure_name can not be None'

        f = self._active_failures.get(failure_name)
        if f != None:
            del self._active_failures[failure_name]
            self._machine.value -= f.get_cost_to_fix()
            self._prepare_next_failures(f)
        else:
            f = self._possible_failures[failure_name]
            self._machine.value -= f.get_false_alert_cost()

    def restored(self, failure_name):
        for c in self._restored_callbacks:
            c()

    def add_failure(self,
                 name = None,
                 get_time_to_failure = None,
                 get_operations_to_failure = None,  # start of n-th operation will enable failure
                 get_time_to_repair = lambda: 0,
                 get_cost_to_fix = lambda: 0,
                 get_false_alert_cost = lambda: 0,
                 is_hard_failure = True,
                 capacity_to_repair = 1,
                 finish_processing_callback = None,
                 failed_callback = None):
        if name == None:
            name = f'Failure_{len(self._possible_failures)}'
        assert not name in self._possible_failures.keys(), \
            f'Failure with that name already exists: {name}'

        mf = MachineFailure(name, get_time_to_failure,
                            get_operations_to_failure, get_time_to_repair, get_cost_to_fix,
                            get_false_alert_cost, is_hard_failure, capacity_to_repair,
                            finish_processing_callback, failed_callback)
        self._possible_failures[name] = mf

    def has_active_hard_failures(self):
        for n, f in self._active_failures.items():
            if f.is_hard_failure:
                return True
        return False

    def _prepare_next_failures(self, failure):
        # If the failure is not scheduled then schedule or reschedule it to occur.
        if failure.scheduled_failure_time == None:
            if failure.remaining_time_to_failure != None:
                failure.scheduled_failure_time = self._env.now + failure.remaining_time_to_failure
                failure.remaining_time_to_failure = None
            elif failure.get_time_to_failure != None:
                failure.scheduled_failure_time = self._env.now + failure.get_time_to_failure()

            if failure.scheduled_failure_time != None:
                self._env.schedule_event(failure.scheduled_failure_time,
                                         self._machine.id,
                                         lambda: self._scheduled_fail(failure),
                                         EventType.FAIL,
                                         f'Timed failure: {failure.name}')

        # Prepare operations based failure
        if (failure.get_operations_to_failure != None
                and failure.operations_to_failure == None):
            failure.operations_to_failure = failure.get_operations_to_failure()

    def _scheduled_fail(self, failure):
        self._active_failures[failure.name] = failure
        # Reset trackers because failure occurred
        failure.scheduled_failure_time = None
        failure.operations_to_failure = None
        failure.operations_since_last_fix = 0

        # Save time to failure if there are other failures waiting to happen.
        if failure.is_hard_failure:
            for n, f in self._active_failures.items():
                if failure != f and f.scheduled_failure_time != None:
                    f.remaining_time_to_failure = max(0,
                          f.scheduled_failure_time - self._env.now)
                    f.scheduled_failure_time = None
            # Failing machine will cancel all currently scheduled events for the machine.
            self._machine.fail()

        if failure.failed_callback != None:
            failure.failed_callback(failure)


class MachineFailure:

    def __init__(self,
                 name,
                 get_time_to_failure,
                 get_operations_to_failure,
                 get_time_to_repair,
                 get_cost_to_fix,
                 get_false_alert_cost,
                 is_hard_failure,
                 capacity_to_repair,
                 finish_processing_callback,
                 failed_callback
                 ):
        assert_callable(get_time_to_failure, True)
        assert_callable(get_operations_to_failure, True)
        assert_callable(get_time_to_repair, False)
        assert_callable(get_cost_to_fix, False)
        assert_callable(get_false_alert_cost, False)
        assert_callable(finish_processing_callback, True)
        assert_callable(failed_callback, True)

        self.name = name
        self.get_time_to_failure = get_time_to_failure
        self.get_operations_to_failure = get_operations_to_failure
        self.is_hard_failure = is_hard_failure
        self.get_time_to_repair = get_time_to_repair
        self.get_cost_to_fix = get_cost_to_fix
        self.get_false_alert_cost = get_false_alert_cost
        self.capacity_to_repair = capacity_to_repair
        self.finish_processing_callback = finish_processing_callback
        self.failed_callback = failed_callback

        self.scheduled_failure_time = None
        self.remaining_time_to_failure = None
        self.operations_since_last_fix = 0
        self.operations_to_failure = None

    @property
    def machine(self):
        return self._machine_status.machine

    def initialize(self, machine_status):
        self._machine_status = machine_status
