from ...utils.utils import assert_callable
from ..simulation import EventType
from .device import Device
from .maintainer import Maintainable


class Machine(Device, Maintainable):
    '''Machine is a Device that can process parts.

    Machine accepts a Part, holds onto it for the duration of a cycle
    (processing time) and then passes it to a downstream Device when
    possible before accepting a new Part to process. To change the Part
    in some way when processing is done use
    add_finish_processing_callback.

    Callback functions can be added to this machine by using functions:
    add_<trigger>_callback such as add_shutdown_callback.

    Machine extends Maintainable class with basic functionality and the
    class should be extended to simulate a more complex maintenance
    scheme.

    Arguments
    ----------
    name: str, default=None
        Name of the Device. If name is None then the Device's name will
        be changed to Machine_<id>
    upstream: list, default=[]
        A list of upstream Devices.
    cycle_time: float, default=0
        How long it takes to process a Part.
    value: float, default=0
        Starting value of the Machine.

    Warning
    -------
    If Machine fails with a Part that hasn't been fully processed then
    the Part is lost. A lost Part can be detected by using
    add_shutdown_callback and checking if part != None in the callback.
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
        ''' How long it takes to process one Part.

        Setting a new cycle time will affect all future process cycles
        but not a cycle that is already in progress.
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
        self._env.add_datapoint('received_parts', self.name, (self._env.now,
                                                              self._part.id,
                                                              self._part.quality,
                                                              self._part.value))
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

    def _finish_processing_part(self, record_produced_part_data = True):
        # If Machine is not operational then the finish processing event
        # should have been paused or cancelled.
        assert self.is_operational(), 'Invalid Machine state.'
        assert self._part != None, f'Input part is missing.'
        assert self._output == None, f'Output part slot is already full.'

        self._output = self._part
        self._schedule_pass_part_downstream()
        self._part = None
        for c in self._finish_processing_callbacks:
            c(self, self._output)
        if record_produced_part_data:
            self._env.add_datapoint('produced_parts', self.name, (self._env.now,
                                                                  self._output.id,
                                                                  self._output.quality,
                                                                  self._output.value))

    def schedule_failure(self, time, message = ''):
        '''Schedule a failure for this Machine.

        When the Machine fails it will lose functionality any Part in
        the middle of processing will be lost.

        Arguments
        ---------
        time: float
            Simulation time when the failure should occur.
        message: str, default=''
            Message that will be associated with the failure event.
            Useful for debugging.
        '''
        self._env.schedule_event(time, self.id, self._fail, EventType.FAIL, message)

    def _fail(self):
        # Processed part (_output) is not lost but input part is.
        lost_part = self._part
        self._part = None
        self._env.add_datapoint('device_failure', self.name,
                (self._env.now, lost_part.id if lost_part else None))
        self._env.cancel_matching_events(asset_id = self.id)
        self._set_waiting_for_part(False)
        for c in self._shutdown_callbacks:
            c(self, True, lost_part)

    def shutdown(self):
        '''Shutdown Part related functionality.

        Part being processed will pause and resume processing when
        Machine is restored. New parts cannot be accepted but any Part
        that was already processed may still move downstream.

        Call restore_functionality to bring Machine back online.

        Warning
        -------
        Do not to call in the middle of another operation from this
        Machine, safest way to call it is to schedule it as a separate
        event.
        '''
        self._is_shut_down = True
        self._env.pause_matching_events(asset_id = self.id)
        self._set_waiting_for_part(False)
        for c in self._shutdown_callbacks:
            c(self, False, None)

    def restore_functionality(self):
        '''Restore Part related functionality and/or recover from a
        failed state.

        Does nothing if machine is not in a shutdown or failed state.
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
        '''Setup a function to be called when the Machine receives a
        new Part.

        | Callback signature: callback(machine, part)
        | machine - Machine to which the callback was added.
        | part - Part that was lost or None if no Part was lost.

        Arguments
        ---------
        callback: function
            Function to be called.
        '''
        assert_callable(callback)
        self._received_part_callbacks.append(callback)

    def add_finish_processing_callback(self, callback):
        '''Setup a function to be called when the Machine finishes
        processing a Part.

        | Callback signature: callback(machine, part)
        | machine - Machine to which the callback was added.
        | part - Part that was received.

        Arguments
        ---------
        callback: function
            Function to be called.
        '''
        assert_callable(callback)
        self._finish_processing_callbacks.append(callback)

    def add_shutdown_callback(self, callback):
        '''Setup a function to be called when the Machine shuts down.

        | Callback signature: callback(machine, part)
        | machine - Machine to which the callback was added.
        | is_failure - True if the shutdown occurred due to failure,
            False otherwise.
        | part - Part that was received.

        Arguments
        ---------
        callback: function
            Function to be called.
        '''
        assert_callable(callback)
        self._shutdown_callbacks.append(callback)

    def add_restored_callback(self, callback):
        '''Setup a function to be called when the Machine is restored
        after a shutdown or failure.

        | Callback signature: callback(machine)
        | machine - Machine to which the callback was added.

        Arguments
        ---------
        callback: function
            Function to be called.
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
