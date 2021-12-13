from ..utils import assert_callable
from ..simulation import EventType


class MachineStatus:

    def __init__(self):
        self._receive_part_callback = None
        self._start_processing_callback = None
        self._finish_processing_callback = None
        self._failed_callback = None
        self._restored_callback = None
        self._machine = None
        self._env = None
        self.possible_failures = {}  # name, MachineFailure
        self.active_failures = {}  # name, MachineFailure

    @property
    def machine(self):
        return self._machine

    def initialize(self, machine, env):
        self._machine = machine
        self._env = env

        for n, f in self.possible_failures.items():
            f.initialize(self)
            self._prepare_next_failures(f)

    def set_receive_part_callback(self, callback):
        assert callable(callback), 'callback needs to be callable.'
        self._receive_part_callback = callback

    def set_start_processing_callback(self, callback):
        assert callable(callback), 'callback needs to be callable.'
        self._start_processing_callback = callback

    def set_finish_processing_callback(self, callback):
        assert callable(callback), 'callback needs to be callable.'
        self._finish_processing_callback = callback

    def set_failed_callback(self, callback):
        assert callable(callback), 'callback needs to be callable.'
        self._failed_callback = callback

    def set_restored_callback(self, callback):
        assert callable(callback), 'callback needs to be callable.'
        self._restored_callback = callback

    def receive_part(self, part):
        if self._receive_part_callback != None:
            self._receive_part_callback(part)

    def start_processing(self, part):
        if self._start_processing_callback != None:
            self._start_processing_callback(part)

        # Check if any failures are happening
        for n, f in self.possible_failures.items():
            if f.operations_to_fail != None:
                f.operations_since_restore += 1
                if f.operations_since_restore >= f.operations_to_fail:
                    f.operations_to_fail = None
                    self._env.schedule_event(self._env.now,
                                             self._machine.id,
                                             lambda: self._scheduled_fail(f, False),
                                             EventType.FAIL)

    def finish_processing(self, part):
        if self._finish_processing_callback != None:
            self._finish_processing_callback(part)

        for n, f in self.active_failures.items():
            if f.finish_processing_callback != None:
                f.finish_processing_callback(part)

    def failed(self):
        if self._failed_callback != None:
            self._failed_callback()

    def restored(self, failure = None):
        for n, f in self.possible_failures.items():
            if n in self.active_failures.keys() and (failure == None or failure == f):
                del self.active_failures[n]
                self._prepare_next_failures(f)

        if self._restored_callback != None:
            self._restored_callback()

    def add_failure(self,
                 name = 'Default Failure Name',
                 get_time_to_failure = None,
                 get_operations_to_failure = None,  # start of n-th operation will enable failure
                 get_time_to_repair = lambda: 0,
                 is_hard_failure = True,
                 capacity_to_repair = 1,
                 finish_processing_callback = None,
                 failed_callback = None):
        mf = MachineFailure(name, get_time_to_failure,
                            get_operations_to_failure, get_time_to_repair,
                            is_hard_failure, capacity_to_repair,
                            finish_processing_callback, failed_callback)
        self.possible_failures[name] = mf

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
                                         lambda: self._scheduled_fail(failure, True),
                                         EventType.FAIL)

        # Prepare operations based failure
        if (failure.get_operations_to_failure != None
                and failure.operations_to_fail == None):
            failure.operations_to_fail = failure.get_operations_to_failure()

    def _scheduled_fail(self, failure, is_timed_failure):
        self.active_failures[failure.name] = failure

        # Save time to failure if there is a scheduled failure.
        if not is_timed_failure and failure.scheduled_failure_time != None:
            failure.remaining_time_to_failure = max(
                    0, failure.scheduled_failure_time - self._env.now)
            failure.scheduled_failure_time = None

        if failure.is_hard_failure:
            self._machine.fail()

        if failure.failed_callback != None:
            failure.failed_callback(failure)


class MachineFailure:

    def __init__(self,
                 name,
                 get_time_to_failure,
                 get_operations_to_failure,
                 get_time_to_repair,
                 is_hard_failure,
                 capacity_to_repair,
                 finish_processing_callback,
                 failed_callback
                 # TODO add other callbacks
                 ):
        assert_callable(get_time_to_failure, True)
        assert_callable(get_operations_to_failure, True)
        assert_callable(get_time_to_repair, False)
        assert_callable(finish_processing_callback, True)
        assert_callable(failed_callback, True)

        self.name = name
        self.get_time_to_failure = get_time_to_failure
        self.get_operations_to_failure = get_operations_to_failure
        self.is_hard_failure = is_hard_failure
        self.get_time_to_repair = get_time_to_repair
        self.capacity_to_repair = capacity_to_repair
        self.finish_processing_callback = finish_processing_callback
        self.failed_callback = failed_callback

        self.scheduled_failure_time = None
        self.remaining_time_to_failure = None
        self.operations_since_restore = 0
        self.operations_to_fail = None

    @property
    def machine(self):
        return self._machine_status.machine

    def initialize(self, machine_status):
        self._machine_status = machine_status
