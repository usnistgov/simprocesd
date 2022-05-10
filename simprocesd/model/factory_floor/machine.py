from ...utils.utils import assert_is_instance, assert_callable
from ..simulation import EventType
from .device import Device


class Machine(Device):
    ''' Machine is a Device that can process parts and has a state
    represented by a status_tracker.

    Arguments:
    name -- name of the machine.
    upstream -- list of upstream devices.
    cycle_time -- how long it takes to complete one process cycle.
    status_tracker -- optional object for tracking operational status of
        the machine.
    value -- starting value of the machine.

    If machine fails with a part that hasn't been fully processed then
    the part is lost. Lost part can be captured by using
    add_failed_callback.
    '''

    def __init__(self,
                 name = None,
                 upstream = [],
                 cycle_time = 0,
                 status_tracker = None,
                 value = 0):
        assert cycle_time >= 0, 'Cycle time cannot be negative.'
        super().__init__(name, upstream, value)

        if status_tracker == None:
            status_tracker = MachineStatusTracker()
        else:
            assert_is_instance(status_tracker, MachineStatusTracker)
        self.status_tracker = status_tracker

        self.cycle_time = self._initial_cycle_time = cycle_time

        self._is_part_processed = False
        self._is_shut_down = False
        self._received_part_callbacks = []
        self._finish_processing_callbacks = []
        self._failed_callbacks = []
        self._restored_callbacks = []

    @property
    def cycle_time(self):
        ''' How long it takes to complete one process cycle.

        Setting a new cycle time will affect all future process cycles.
        An already started process cycle will not be affected.
        '''
        return self._cycle_time

    @cycle_time.setter
    def cycle_time(self, new_value):
        self._cycle_time = new_value

    def is_operational(self):
        return not self._is_shut_down and self.status_tracker.is_operational()

    def initialize(self, env):
        super().initialize(env)
        self.status_tracker.initialize(self, env)
        self.cycle_time = self._initial_cycle_time
        self._is_part_processed = False
        self._is_shut_down = False

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
            self._env.now + self.cycle_time,
            self.id,
            self._finish_processing_part,
            EventType.FINISH_PROCESSING,
            f'By {self.name}'
        )

    def _finish_processing_part(self):
        if not self.is_operational(): return
        assert self._part != None, f'Input part is missing.'
        assert self._output == None, f'Output part slot is already full.'

        self._output = self._part
        self._schedule_pass_part_downstream()
        self._part = None
        for c in self._finish_processing_callbacks:
            c(self._output)
        self._env.add_datapoint('produced_parts', self.name, (self._env.now, self._output.quality))

    def schedule_failure(self, time, message):
        ''' Schedule a failure for this machine.

        Arguments:
        time -- when the failure will be scheduled to occur.
        message -- message that will be associated with the event.
            Useful for debugging.
        '''
        self._env.schedule_event(time, self.id, self._fail, EventType.FAIL, message)

    def _fail(self):
        # Processed part (_output) is not lost but input part is.
        lost_part = self._part
        self._part = None
        self._env.cancel_matching_events(asset_id = self.id)
        self._set_waiting_for_part(False)
        for c in self._failed_callbacks:
            c(lost_part)

    def shutdown(self):
        ''' Make sure not to call in the middle of another Machine
        operation, safest way is to schedule it as a separate event.

        WARNING: Part being processed will pause and resume when
        machine is restored.
        '''
        self._is_shut_down = True
        self._env.pause_matching_events(asset_id = self.id)
        self._set_waiting_for_part(False)

    def restore_functionality(self):
        ''' Restore machine to an operational state after a shutdown()
        or after a maintained/repaired failure. If status tracker is not
        operational nothing will be done.
        '''
        if not self.status_tracker.is_operational():
            return
        self._is_shut_down = False
        self._env.unpause_matching_events(asset_id = self.id)
        if self._output != None:
            self._schedule_pass_part_downstream()
        elif self._part == None:
            self.notify_upstream_of_available_space()

        for c in self._restored_callbacks:
            c()

    def add_receive_part_callback(self, callback):
        '''Accepts one argument: received part.
        callback(part)
        '''
        assert_callable(callback)
        self._received_part_callbacks.append(callback)

    def add_finish_processing_callback(self, callback):
        '''Accepts one argument: part that has just been processed.
        callback(part)
        '''
        assert_callable(callback)
        self._finish_processing_callbacks.append(callback)

    def add_failed_callback(self, callback):
        '''Accepts one argument: part in the machine that has not been
        processed yet or None if there is no such part in the machine.
        The part is removed from the machine when machine fails.
        callback(part)
        '''
        assert_callable(callback)
        self._failed_callbacks.append(callback)

    def add_restored_callback(self, callback):
        '''Accepts no arguments.
        callback()
        '''
        assert_callable(callback)
        self._restored_callbacks.append(callback)


class MachineStatusTracker:
    ''' Base class for representing the status of the machine.
    '''

    def __init__(self):
        self._machine = None
        self._env = None

    @property
    def machine(self):
        ''' Machine whose status this represents.
        '''
        return self._machine

    def initialize(self, machine, env):
        self._machine = machine
        self._env = env

    def maintain(self, maintenance_tag):
        ''' Perform maintenance. Called by Maintainer when it performs
        maintenance on the associated Machine.

        Arguments:
        maintenance_tag -- maintenance identifier. Supports any type.
        '''
        pass

    def get_time_to_maintain(self, maintenance_tag):
        ''' Return how long it will take to perform the maintenance.

        Arguments:
        maintenance_tag -- maintenance identifier. Supports any type.
        '''
        return 0

    def get_capacity_to_maintain(self, maintenance_tag):
        ''' Return how much maintenance capacity is needed to perform
        the maintenance.

        Arguments:
        maintenance_tag -- maintenance identifier. Supports any type.
        '''
        return 0

    def is_operational(self):
        ''' Return True if the status of the machine does not prevent it
        from operating, False otherwise.
        '''
        return True
