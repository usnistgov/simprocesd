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
    Multiple callbacks on the same trigger are called in the order they
    were added.

    Machine extends Maintainable class with basic functionality and the
    class should be extended to simulate a more complex maintenance
    scheme.

    Arguments
    ---------
    name: str, default=None
        Name of the Device. If name is None then the Device's name will
        be changed to Machine_<id>
    upstream: list, default=None
        A list of upstream Devices.
    cycle_time: float, default=0
        How long it takes to process a Part.
    value: float, default=0
        Starting value of the Machine.
    resources_for_processing: Dictionary, default=None
        A dictionary specifying resources needed for this Machine to
        process Parts. Each key-value entry in the dictionary identifies
        what resource (key) needs to be reserved and how much(value) of
        it needs to be reserved.
        These resources will be reserved at the beginning of Part
        processing and they will be released when the processing is
        done.

    Warning
    -------
    If Machine fails with a Part that hasn't been fully processed then
    the Part is lost. A lost Part can be detected by using
    add_shutdown_callback and checking if part != None in the callback.
    '''

    def __init__(self,
                 name = None,
                 upstream = None,
                 cycle_time = 0,
                 value = 0,
                 resources_for_processing = None):
        super().__init__(name, upstream, value)

        self.cycle_time = cycle_time
        self._is_shut_down = False
        self._resources_for_processing = resources_for_processing
        self._reserved_resources = None
        self._waiting_for_resources = False

        self._finish_processing_callbacks = []
        self._shutdown_callbacks = []
        self._restored_callbacks = []

        self._uptime = 0
        self._last_restore = 0
        self._time_in_use = 0
        self._last_use_start = None
        self._next_cycle_time_offset = 0

    @property
    def cycle_time(self):
        ''' How long it takes to process one Part.

        Setting a new cycle time will affect all future process cycles
        but not a cycle that is already in progress.
        '''
        return self._cycle_time

    @cycle_time.setter
    def cycle_time(self, new_value):
        assert new_value >= 0, 'Cycle time cannot be negative.'
        self._cycle_time = new_value

    @property
    def uptime(self):
        ''' How much time has the Machine been operational (not
        shutdown).
        '''
        if self._last_restore == None:
            return self._uptime
        else:
            return self._uptime + (self.env.now - self._last_restore)

    @property
    def utilization_time(self):
        ''' How much time has the Machine spent on processing Parts.
        '''
        if self._last_use_start == None:
            return self._time_in_use
        else:
            return self._time_in_use + (self.env.now - self._last_use_start)

    def initialize(self, env):
        if self._env == None:
            # First time initialize.
            self._initial_cycle_time = self.cycle_time
            self._initial_next_cycle_time_offset = self._next_cycle_time_offset
        else:
            # Simulation is resetting, restore starting values.
            self.cycle_time = self._initial_cycle_time
            self._next_cycle_time_offset = self._initial_next_cycle_time_offset

        super().initialize(env)
        self._is_shut_down = False
        self._uptime = 0
        self._last_restore = self.env.now
        self._time_in_use = 0
        self._last_use_start = None
        self._reserved_resources = None

    def _can_accept_part(self, part):
        '''Override the standard function for deciding whether to accept
        an incoming Part. This version also tries to reserve the needed
        resources before accepting the Part.
        '''
        if not super()._can_accept_part(part):
            return False
        # Reserving resources if any are needed for Part processing.
        if self._resources_for_processing != None and self._reserved_resources == None:
            self._reserved_resources = self.env.resource_manager.reserve_resources(
                    self._resources_for_processing)
            if self._reserved_resources == None:
                if not self._waiting_for_resources:
                    self.env.resource_manager.reserve_resources_with_callback(self._resources_for_processing,
                                                                              self._reserve_resource_callback)
                    self._waiting_for_resources = True
                return False
        return True

    def _try_move_part_to_output(self):
        if self._part != None and self._output == None:
            self._last_use_start = self.env.now
            self._schedule_finish_processing_part()

    def _schedule_finish_processing_part(self, time_offset = 0):
        '''If the final cycle time <= 0 then _finish_processing_part
        will be called immediately.
        '''
        next_cycle_time = max(0, self.cycle_time + self._next_cycle_time_offset + time_offset)
        self._next_cycle_time_offset = 0
        if next_cycle_time <= 0:
            self._finish_processing_part()
        else:
            self._env.schedule_event(
                self._env.now + next_cycle_time,
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
        self._part = None
        self._time_in_use += self.env.now - self._last_use_start
        self._last_use_start = None

        if self._reserved_resources != None:
            self._env.schedule_event(self._env.now,
                                     self.id,
                                     self._release_resources_if_idle,
                                     EventType.RELEASE_RESERVED_RESOURCES,
                                     f'By {self.name}')

        for c in self._finish_processing_callbacks:
            c(self, self._output)

        if self._output == None:
            self.notify_upstream_of_available_space()
        else:
            self._schedule_pass_part_downstream()
            if record_produced_part_data:
                self._env.add_datapoint('produced_part', self.name, (self._env.now,
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
        self._release_reserved_resources()
        self._env.add_datapoint('device_failure', self.name,
                (self._env.now, lost_part.id if lost_part else None))
        self._shutdown(True, lost_part)

    def shutdown(self):
        '''Shutdown Part related functionality.

        Part being processed will pause and resume processing when
        Machine is restored. New parts cannot be accepted but any Part
        that was already processed may still move downstream.

        Does nothing if machine is already in a shutdown or failed
        state.

        Call restore_functionality to bring Machine back online.

        Warning
        -------
        Do not to call in the middle of another operation from this
        Machine, safest way to call it is to schedule it as a separate
        event.
        '''
        self._shutdown(False, None)

    def _shutdown(self, is_failure, lost_part):
        if self._is_shut_down:
            return
        self._is_shut_down = True
        if is_failure:
            self._env.cancel_matching_events(asset_id = self.id)
        else:
            self._env.pause_matching_events(asset_id = self.id)

        self._uptime += self.env.now - self._last_restore
        self._last_restore = None
        if self._last_use_start != None:
            self._time_in_use += self.env.now - self._last_use_start
            self._last_use_start = None

        self._set_waiting_for_part(False)
        for c in self._shutdown_callbacks:
            c(self, is_failure, lost_part)

    def restore_functionality(self):
        '''Restore Part related functionality and/or recover from a
        failed state.

        Does nothing if machine is not in a shutdown or failed state.
        '''
        if not self._is_shut_down:
            return
        self._is_shut_down = False
        self._last_restore = self.env.now
        self._env.unpause_matching_events(asset_id = self.id)
        # Ensure part flow is restored.
        if self._output != None:
            self._schedule_pass_part_downstream()
        elif self._part == None:
            self.notify_upstream_of_available_space()
        # Restart utilization tracker if a part is being processed.
        if self._part != None:
            self._last_use_start = self.env.now

        for c in self._restored_callbacks:
            c(self)

    def is_operational(self):
        return not self._is_shut_down

    def _reserve_resource_callback(self, request):
        '''When requested resources are available the Machine will
        signal that it can receive a Part. When a new Part is offered to
        the Machine, it will try to reserve the resources.
        '''
        self._waiting_for_resources = False
        self.notify_upstream_of_available_space()

    def _release_resources_if_idle(self):
        if not self.is_operational() or self._part == None:
            self._release_reserved_resources()

    def _release_reserved_resources(self):
        if self._reserved_resources != None:
            self._reserved_resources.release()
            self._reserved_resources = None

    def offset_next_cycle_time(self, offset):
        '''Offset the cycle time of the next processing cycle.

        The effects are cumulative across multiple calls of
        offset_next_cycle_time. If the cycle time plus the final offset
        are less than 0 then a cycle time of 0 will be used.

        Once the next cycle starts the offset will reset to 0.

        Arguments
        ---------
        offset: float
            By how much to offset the cycle time of the next processing
            cycle.
        '''
        self._next_cycle_time_offset += offset

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
