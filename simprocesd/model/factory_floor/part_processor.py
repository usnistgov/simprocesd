from ...utils.utils import assert_callable
from ..simulation import EventType
from .part_handler import PartHandler
from .maintainer import Maintainable


class PartProcessor(PartHandler, Maintainable):
    '''Production device that can modify Parts.

    Extends PartHandler to closer simulate a production machine:
    - Parts can be modified in a callback function by adding it with
    add_finish_processing_callback. When the processing cycle finishes
    the callback will be called with the Part as a parameter.
    - Implements Maintainable so it can be a target of Maintainer's
    work orders.
    - Can require resources from ResourceManager in order to process
    Parts. If specified resources are unavailable then new Parts will
    not be accepted by the PartProcessor.

    Callback functions can be added to this machine by using functions:
    add_<trigger>_callback such as add_shutdown_callback.
    Multiple callbacks on the same trigger are called in the order they
    were added.

    PartProcessor extends Maintainable class with basic functionality and the
    class should be extended to simulate a more complex maintenance
    scheme.

    Arguments
    ---------
    name: str, default=None
        Name of the Asset. If name is None then a default name will be
        used: <class_name>_<asset_id>
    upstream: list of PartFlowController, default=None
        List of PartFlowControllers from which Parts can be received.
    cycle_time: float, default=0
        How long it takes to process a Part.
    value: float, default=0
        Starting value of the Asset.
    resources_for_processing: Dictionary, default=None
        A dictionary specifying resources needed for processing Parts.
        Each key-value entry in the dictionary identifies what
        resource (key) needs to be reserved and how much(value) of
        it needs to be reserved.
        These resources will be reserved before a Part is accepted
        and they will be released when the processing of the Part is
        done. If the processed Part can be passed and a new Part is
        provided immediately then the PartProcessor will skip
        releasing and re-acquiring the resources.

    Note
    -------
    If PartProcessor fails with a Part that hasn't been fully
    processed then the Part is lost. A lost Part can be captured by
    using add_shutdown_callback.
    '''

    def __init__(self,
                 name = None,
                 upstream = None,
                 cycle_time = 0,
                 value = 0,
                 resources_for_processing = None):
        super().__init__(name, upstream, cycle_time, value)
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

    @property
    def uptime(self):
        '''Total time that the PartProcessor been operational (not
        shutdown).
        '''
        if self._last_restore == None:
            return self._uptime
        else:
            return self._uptime + (self.env.now - self._last_restore)

    @property
    def utilization_time(self):
        '''Total time that the PartProcessor spent processing Parts.
        '''
        if self._last_use_start == None:
            return self._time_in_use
        else:
            return self._time_in_use + (self.env.now - self._last_use_start)

    def initialize(self, env):
        super().initialize(env)
        self._last_restore = self.env.now

    def is_operational(self):
        return not self._is_shut_down

    def _can_accept_part(self, part):
        '''Override the standard function for deciding whether to accept
        an incoming Part. This version also tries to reserve the needed
        resources before accepting the Part.
        '''
        if not super()._can_accept_part(part):
            return False
        # Reserving resources if any are needed and none are
        # already reserved.
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
        if self.is_operational() and self._part != None and self._output == None:
            self._last_use_start = self.env.now
            self._schedule_finish_cycle()

    def _finish_cycle(self):
        super()._finish_cycle()
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
        self._env.add_datapoint('produced_part', self.name, (self._env.now,
                                                             self._output.id,
                                                             self._output.quality,
                                                             self._output.value))

    def schedule_failure(self, time, message = ''):
        '''Schedule a failure for this PartProcessor.

        When the PartProcessor fails it will lose functionality and
        any Part in the middle of processing will be lost.
        For capturing the lost Part see add_shutdown_callback.

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
        '''Shutdown the PartProcessor.

        Part being processed will pause and resume processing when
        PartProcessor is restored. New parts cannot be accepted.
        Does nothing if the PartProcessor is already in a shutdown or
        failed state.

        Call restore_functionality to bring PartProcessor back online.

        Warning
        -------
        Do not to call in the middle of another operation from this
        PartProcessor, safest way to call it is to schedule it as a separate
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
        '''Restore the PartProcessor from a shutdown and failed
        states.

        Does nothing if not in a shutdown or failed states.
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

    def _reserve_resource_callback(self, resource_manager, request):
        '''Indicates that the needed resources became available.
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

    def add_finish_processing_callback(self, callback):
        '''Register a function to be called when the PartProcessor
        finishes processing a Part.

        | Callback signature: callback(machine, part)
        | part_processor - PartProcessor doing the processing.
        | part - Part that was processed.

        Arguments
        ---------
        callback: function
            Function to be called.
        '''
        assert_callable(callback)
        self._finish_processing_callbacks.append(callback)

    def add_shutdown_callback(self, callback):
        '''Register a function to be called when the PartProcessor
        shuts down.

        | Callback signature: callback(machine, part)
        | part_processor - PartProcessor that was shutdown.
        | is_failure - True if the shutdown occurred due to failure,
            False otherwise.
        | part - Part that was lost or None if no Part was lost.

        Arguments
        ---------
        callback: function
            Function to be called.
        '''
        assert_callable(callback)
        self._shutdown_callbacks.append(callback)

    def add_restored_callback(self, callback):
        '''Register a function to be called when the PartProcessor is
        restored after a shutdown or failure.

        | Callback signature: callback(machine)
        | part_processor - PartProcessor that was restored.

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
