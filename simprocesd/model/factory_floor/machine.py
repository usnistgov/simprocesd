from ...utils.utils import assert_callable
from ..simulation import EventType
from .device import Device
from .maintainer import Maintainable


class Machine(Device, Maintainable):
    ''' Machine is a Device that can process parts.

    Arguments:
    name -- name of the machine.
    upstream -- list of upstream devices.
    cycle_time -- how long it takes to complete one process cycle.
    value -- starting value of the machine.

    If machine fails with a part that hasn't been fully processed then
    the part is lost. Lost part can be captured by using
    add_shutdown_callback.
    '''

    def __init__(self,
                 name = None,
                 upstream = [],
                 cycle_time = 0,
                 value = 0):
        assert cycle_time >= 0, 'Cycle time cannot be negative.'
        super().__init__(name, upstream, value)

        self.cycle_time = self._initial_cycle_time = cycle_time

        self._is_part_processed = False
        self._is_shut_down = False
        self._received_part_callbacks = []
        self._finish_processing_callbacks = []
        self._shutdown_callbacks = []
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
        return not self._is_shut_down

    def initialize(self, env):
        super().initialize(env)
        self.cycle_time = self._initial_cycle_time
        self._is_part_processed = False
        self._is_shut_down = False

    def _on_received_new_part(self):
        self._env.add_datapoint('received_parts', self.name, (self._env.now, self._part.quality))
        super()._on_received_new_part()
        for c in self._received_part_callbacks:
            c(self, self._part)

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
            c(self, self._output)
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
        for c in self._shutdown_callbacks:
            c(self, True, lost_part)

    def shutdown(self):
        ''' Make sure not to call in the middle of another Machine
        operation, safest way is to schedule it as a separate event.

        WARNING: Part being processed will pause and resume when
        machine is restored.
        '''
        self._is_shut_down = True
        self._env.pause_matching_events(asset_id = self.id)
        self._set_waiting_for_part(False)
        for c in self._shutdown_callbacks:
            c(self, False, None)

    def restore_functionality(self):
        ''' Restore machine to an operational state after a shutdown()
        or after a maintained/repaired failure.
        Does nothing if machine is not in a shut down state.
        '''
        if not self._is_shut_down:
            return
        self._is_shut_down = False
        self._env.unpause_matching_events(asset_id = self.id)
        if self._output != None:
            self._schedule_pass_part_downstream()
        elif self._part == None:
            self.notify_upstream_of_available_space()

        for c in self._restored_callbacks:
            c(self)

    def add_receive_part_callback(self, callback):
        ''' Setup a function to be called when the machine receives a
        a new part.
        Function signature: callback(machine, part)

        Arguments:
        callback -- function to be called.
            callback arguments:
            machine - machine to which the callback was added.
            part - part that was received.
        '''
        assert_callable(callback)
        self._received_part_callbacks.append(callback)

    def add_finish_processing_callback(self, callback):
        ''' Setup a function to be called when the machine finishes
        processing a part.
        Function signature: callback(machine, part)

        Arguments:
        callback -- function to be called.
            callback arguments:
            machine - machine to which the callback was added.
            part - part that has just been processed.
        '''
        assert_callable(callback)
        self._finish_processing_callbacks.append(callback)

    def add_shutdown_callback(self, callback):
        ''' Setup a function to be called when the machine shuts down.
        Function signature: callback(machine, is_failure, part)

        Arguments:
        callback -- function to be called.
            callback arguments:
            machine - machine to which the callback was added.
            is_failure - True if the shutdown occurred due to failure,
                False otherwise.
            part - part object that was lost when the machine shut
                down or None if no part was lost.
        '''
        assert_callable(callback)
        self._shutdown_callbacks.append(callback)

    def add_restored_callback(self, callback):
        ''' Setup a function to be called when the machine is restored
        after a shutdown.
        Function signature: callback(machine)

        Arguments:
        callback -- function to be called.
            callback arguments:
            machine - machine to which the callback was added.
        '''
        assert_callable(callback)
        self._restored_callbacks.append(callback)

    # Beginning of Maintainable function overrides.
    def get_work_order_duration(self, tag):
        return 0

    def get_work_order_capacity(self, tag):
        return 0

    def get_work_order_cost(self, tag):
        return 0

    def start_work(self, tag):
        self.shutdown()

    def end_work(self, tag):
        self.restore_functionality()
    # End of Maintainable function overrides.
