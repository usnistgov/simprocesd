from ...utils.utils import assert_is_instance, assert_callable
from ..simulation import EventType
from .machine_base import MachineBase


class Machine(MachineBase):
    ''' Machine that has a state and a configurable cycle time.

    WARNING: This machine can hold up to 2 parts, 1 processed part and
    one input part that will not begin to be processed until the
    processed part is passed downstream.
    See MachineBase class for more information.
    '''

    def __init__(self,
                 name = None,
                 upstream = [],
                 cycle_time = 1.0,
                 status_tracker = None,
                 value = 0):
        assert cycle_time >= 0, 'Cycle time cannot be negative.'
        super().__init__(name, upstream, value)

        if status_tracker == None:
            status_tracker = MachineStatusTracker()
        else:
            assert_is_instance(status_tracker, MachineStatusTracker)
        self.status_tracker = status_tracker

        self._cycle_time = cycle_time

        self._is_part_processed = False
        self._is_shut_down = False
        self._received_part_callbacks = []
        self._finish_processing_callbacks = []
        self._failed_callbacks = []
        self._restored_callbacks = []

    @property
    def is_operational(self):
        return not self._is_shut_down and self.status_tracker.is_operational()

    def initialize(self, env):
        super().initialize(env)
        self.status_tracker.initialize(self, env)

    def _on_received_new_part(self):
        self._env.add_datapoint('received_parts', self.name, (self._env.now, self._part.quality))
        super()._on_received_new_part()
        for c in self._received_part_callbacks:
            c(self._part)

    def _try_move_part_to_output(self):
        if self._part != None and self._output == None:
            self._schedule_finish_processing_part()

    def _schedule_finish_processing_part(self):
        self._env.schedule_event(
            self._env.now + self._cycle_time,
            self.id,
            self._finish_processing_part,
            EventType.FINISH_PROCESSING,
            f'By {self.name}'
        )

    def _finish_processing_part(self):
        if not self.is_operational: return
        assert self._part != None, f'Input part is missing.'
        assert self._output == None, f'Output part slot is already full.'

        self._output = self._part
        self._part = None
        self._schedule_pass_part_downstream()
        self._notify_upstream_of_available_space()
        for c in self._finish_processing_callbacks:
            c(self._output)
        self._env.add_datapoint('produced_parts', self.name, (self._env.now, self._output.quality))

    def schedule_failure(self, time, message):
        self._env.schedule_event(time, self.id, self._fail, EventType.FAIL, message)

    def _fail(self):
        # Processed part (_output) is not lost but input part is.
        self._part = None
        self._env.cancel_matching_events(asset_id = self.id)
        for c in self._failed_callbacks:
            c()

    def shutdown(self):
        ''' Make sure not to call in the middle of another Machine
        operation, safest way is to schedule it as a separate event.
        '''
        self._is_shut_down = True
        self._env.pause_matching_events(asset_id = self.id)

    def restore_functionality(self):
        if not self.status_tracker.is_operational():
            return
        self._is_shut_down = False
        self._env.unpause_matching_events(asset_id = self.id)
        if self._output != None:
            self._schedule_pass_part_downstream()
        if self._part == None:
            self._notify_upstream_of_available_space()

        for c in self._restored_callbacks:
            c()

    def add_receive_part_callback(self, callback):
        '''Accepts one argument: part
        callback(part)
        '''
        assert_callable(callback)
        self._received_part_callbacks.append(callback)

    def add_finish_processing_callback(self, callback):
        '''Accepts one argument: part
        callback(part)
        '''
        assert_callable(callback)
        self._finish_processing_callbacks.append(callback)

    def add_failed_callback(self, callback):
        '''Accepts no arguments
        callback()
        '''
        assert_callable(callback)
        self._failed_callbacks.append(callback)

    def add_restored_callback(self, callback):
        '''Accepts no arguments
        callback()
        '''
        assert_callable(callback)
        self._restored_callbacks.append(callback)


class MachineStatusTracker:

    def __init__(self):
        self._machine = None
        self._env = None

    @property
    def machine(self):
        return self._machine

    def initialize(self, machine, env):
        self._machine = machine
        self._env = env

    def maintain(self, maintenance_tag):
        pass

    def get_time_to_maintain(self, maintenance_tag):
        return 0

    def get_capacity_to_maintain(self, maintenance_tag):
        return 0

    def is_operational(self):
        return True
