from .asset import Asset
from .machine_status import MachineStatus
from ..simulation import EventType
from ..utils import assert_is_instance


class MachineAsset(Asset):
    '''Base class for machine assets in the system.'''

    def __init__(self,
                 name = None,
                 upstream = [],
                 cycle_time = 1.0,
                 machine_status = MachineStatus(),
                 **kwargs):
        super().__init__(name, **kwargs)

        assert_is_instance(machine_status, MachineStatus)
        self.machine_status = machine_status

        self._upstream = upstream
        self._downstream = []
        self._cycle_time = cycle_time

        self._part = None
        self._waiting_for_part_availability = False
        self._output_part = None
        self._waiting_for_output_availability = False
        self._env = None
        self._is_operational = True

    @property
    def is_operational(self):
        return self._is_operational

    @property
    def upstream(self):
        return self._upstream

    @upstream.setter
    def upstream(self, upstream):
        assert_is_instance(upstream, list)
        self._upstream = upstream

    def initialize(self, env):
        super().initialize(env)

        self.machine_status.initialize(env)

        for obj in self._upstream:
            assert_is_instance(obj, MachineAsset)
            obj._add_downstream(self)

        self._schedule_get_part_from_upstream();

    def _add_downstream(self, downstream):
        assert_is_instance(downstream, MachineAsset)
        self._downstream.append(downstream)

    def _schedule_get_part_from_upstream(self, time = None):
        self._waiting_for_part_availability = False
        self._env.schedule_event(time if time != None else self._env.now, self.id,
                                 self._get_part_from_upstream, EventType.GET_PART)

    def _get_part_from_upstream(self):
        if not self._is_operational: return
        assert self._part == None, \
               f"Bad state, there should not be a part {self._part.name}."

        for ups in self._upstream:
            self._part = ups._take_part()
            if self._part != None:
                self._part.routing_history.append(self.name)
                self._schedule_start_processing_part()
                self.machine_status.got_new_part(self._part)
                return
        self._waiting_for_part_availability = True

    def _schedule_start_processing_part(self, time = None):
        self._waiting_for_output_availability = False
        self._env.schedule_event(time if time != None else self._env.now, self.id,
                                 self._start_processing_part, EventType.START_PROCESSING)

    def _start_processing_part(self):
        if not self._is_operational: return
        assert self._part != None, "Bad state, part should be available."

        if self._output_part != None:
            self._waiting_for_output_availability = True
        else:
            self.machine_status.started_processing_part(self._part)
            self._schedule_finish_processing_part()

    def _schedule_finish_processing_part(self, time = None):
        self._env.schedule_event(
            time if time != None else self._env.now + self._cycle_time,
            self.id,
            self._finish_processing_part,
            EventType.FINISH_PROCESSING
        )

    def _finish_processing_part(self):
        assert self._output_part == None, \
              f"Bad state, there should not be an output {output.name}."
        assert self._part != None, "Bad state, part should be available."

        if self._is_operational:
            self._output_part = self._part
            temp = self._part
            self._part = None

            self.machine_status.finished_processing_part(temp)
            self._schedule_get_part_from_upstream()

            self._notify_downstream_of_available_part()

    def _notify_downstream_of_available_part(self):
        for down in self._downstream:
            down._part_available_upstream()

    def _part_available_upstream(self):
        if self._is_operational and self._waiting_for_part_availability:
            self._schedule_get_part_from_upstream()

    def _take_part(self):
        # Output assumes the part was already passed forward so
        # we do not check if machine is still operational.
        if self._output_part == None:
            return None

        temp = self._output_part
        self._output_part = None
        if self.is_operational and self._waiting_for_output_availability:
            self._schedule_start_processing_part()
        return temp

    def fail(self):
        self.part = None  # part being processed is lost
        self._is_operational = False

        self._env.cancel_matching_events(asset_id = self.id)
        self.machine_status.failed()

    def shutdown_machine(self, is_pause = False):
        self._is_operational = False

        if not is_pause:
            self.part = None
            self._env.cancel_matching_events(location = self.name)
        else:
            # TODO pause processing so it can be resumed later and resume it later
            raise NotImplementedError("Pause is not implemented.")

    def restore_functionality(self):
        assert not self._is_operational, \
               f'Restore functionality called when {self.name} is operational.'
        self._is_operational = True

        # TODO if machine was paused need to resume processing of current part
        self._schedule_get_part_from_upstream()
        self.machine_status.restored()

