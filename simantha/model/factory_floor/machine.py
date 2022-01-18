from .asset import Asset
from ..simulation import EventType
from ...utils.utils import assert_is_instance, assert_callable


class Machine(Asset):
    '''Base class for machine assets in the system.'''

    def __init__(self,
                 name = None,
                 upstream = [],
                 cycle_time = 1.0,
                 status_tracker = None,
                 **kwargs):
        super().__init__(name, **kwargs)

        if status_tracker == None:
            status_tracker = MachineStatusTracker()
        else:
            assert_is_instance(status_tracker, MachineStatusTracker)
        self.status_tracker = status_tracker

        self._downstream = []
        self._upstream = []  # Needed for the setter to work
        self.upstream = upstream
        self._cycle_time = cycle_time

        self._part = None
        self._waiting_for_part_availability = False
        self._output_part = None
        self._env = None
        self._is_shut_down = False
        self._receive_part_callbacks = []
        self._finish_processing_callbacks = []
        self._failed_callbacks = []
        self._restored_callbacks = []

    @property
    def is_operational(self):
        return not self._is_shut_down and self.status_tracker.is_operational()

    @property
    def upstream(self):
        return self._upstream

    @upstream.setter
    def upstream(self, upstream):
        assert_is_instance(upstream, list)
        for up in self._upstream:
            up._remove_downstream(self)

        self._upstream = upstream
        for up in self._upstream:
            assert_is_instance(up, Machine)
            up._add_downstream(self)

    def initialize(self, env):
        super().initialize(env)

        self.status_tracker.initialize(self, env)
        self._schedule_get_part_from_upstream();

    def _add_downstream(self, downstream):
        assert_is_instance(downstream, Machine)
        self._downstream.append(downstream)

    def _remove_downstream(self, downstream):
        assert_is_instance(downstream, Machine)
        self._downstream.remove(downstream)

    def _schedule_get_part_from_upstream(self, time = None):
        self._waiting_for_part_availability = False
        self._env.schedule_event(time if time != None else self._env.now, self.id,
                                 self._get_part_from_upstream, EventType.GET_PART)

    def _get_part_from_upstream(self):
        if not self.is_operational: return
        assert self._part == None, \
               f'Bad state, a part is already present:{self._part.name}.'
        assert self._output_part == None, \
               f'Bad state, a part is already present in output:{self._part.name}.'

        for ups in self._upstream:
            self._part = ups._take_part()
            if self._part != None:
                self._on_received_new_part()
                return
        # Could not get a part from upstream.
        self._waiting_for_part_availability = True

    def _on_received_new_part(self):
        self._part.routing_history.append(self.name)
        self._schedule_finish_processing_part()

        for c in self._receive_part_callbacks:
            c(self._part)

    def _schedule_finish_processing_part(self, time = None):
        self._env.schedule_event(
            time if time != None else self._env.now + self._cycle_time,
            self.id,
            self._finish_processing_part,
            EventType.FINISH_PROCESSING
        )

    def _finish_processing_part(self):
        if not self.is_operational: return
        assert self._output_part == None, \
              f'Bad state, there should not be an output {self._output_part.name}.'
        assert self._part != None, 'Bad state, part should be available.'

        self._output_part = self._part
        self._part = None
        self._notify_downstream_of_available_part()

        for c in self._finish_processing_callbacks:
            c(self._output_part)

    def _notify_downstream_of_available_part(self):
        for down in self._downstream:
            down._part_available_upstream()

    def _part_available_upstream(self):
        if self.is_operational and self._waiting_for_part_availability:
            self._schedule_get_part_from_upstream()

    def _take_part(self):
        if not self.is_operational or self._output_part == None:
            return None

        temp = self._output_part
        self._output_part = None
        self._schedule_get_part_from_upstream()
        return temp

    def schedule_failure(self, time = None):
        self._env.schedule_event(time if time != None else self._env.now,
                                 self.id,
                                 self.fail,
                                 EventType.FAIL)

    def fail(self):
        self._part = None  # part being processed is lost
        self._waiting_for_part_availability = self._output_part == None
        self._env.cancel_matching_events(asset_id = self.id)
        for c in self._failed_callbacks:
            c()

    def shutdown(self):
        '''Make sure not to call in the middle of another Machine
        operation, safest way is to schedule it as a separate event.
        '''
        self._is_shut_down = True
        self._env.pause_matching_events(asset_id = self.id)

    def restore_functionality(self):
        if not self.status_tracker.is_operational():
            return
        self._is_shut_down = False
        self._env.unpause_matching_events(asset_id = self.id)
        if self._waiting_for_part_availability:
            self._schedule_get_part_from_upstream()

        for c in self._restored_callbacks:
            c()

    def add_receive_part_callback(self, callback):
        '''Accepts one argument: part
        callback(part)
        '''
        assert_callable(callback)
        self._receive_part_callbacks.append(callback)

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

    def get_time_to_repair(self, fault_name):
        pass

    def get_capacity_to_repair(self, fault_name):
        pass

    def is_operational(self):
        return True
