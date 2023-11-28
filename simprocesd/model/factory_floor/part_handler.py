from ...utils.utils import assert_callable
from ..simulation import EventType
from .part_flow_controller import PartFlowController


class PartHandler(PartFlowController):
    '''Production line device that can hold a Part for a specified
    duration.

    Can hold up to 1 Part and has a cycle time delay between accepting
    a Part and passing that Part downstream.

    Arguments
    ---------
    name: str, default=None
        Name of the Asset. If name is None then a default name will be
        used: <class_name>_<asset_id>
    upstream: list of PartFlowController, default=None
        List of devices from which Parts can be received.
    cycle_time: float, default=0
        How long an accepted Part will be held before trying to
        pass it downstream.
    value: float, default=0
        Starting value of the Asset.
    '''

    def __init__(self, name = None, upstream = None, cycle_time = 0, value = 0):
        self._waiting_for_part_since = None
        super().__init__(name, upstream, value)
        self.cycle_time = cycle_time
        self._next_cycle_time_offset = 0
        self._part = None
        self._output = None
        self._received_part_callbacks = []
        self._waiting_for_downstream_space = False

    def initialize(self, env):
        super().initialize(env)
        self._set_waiting_for_part(True, True)

    @property
    def cycle_time(self):
        '''Time between accepting a Part and passing it downstream.

        Setting a new cycle time will affect all future cycles but
        not a cycle that is already in progress. A cycle starts when
        a Part is accepted.
        '''
        return self._cycle_time

    @cycle_time.setter
    def cycle_time(self, new_value):
        assert new_value >= 0, 'Cycle time cannot be negative.'
        self._cycle_time = new_value

    @property
    def waiting_for_part_start_time(self):
        '''Simulation time of when this device started waiting for the
        next Part. Is None if not currently waiting for a Part.
        '''
        return self._waiting_for_part_since

    def set_upstream(self, new_upstream):
        # Reset waiting time if already waiting for a Part.
        if self.waiting_for_part_start_time != None and self._env != None:
            self._set_waiting_for_part(True, True)
        super().set_upstream(new_upstream)

    def offset_next_cycle_time(self, offset):
        '''Offset the cycle time only for the next cycle.

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

    def notify_upstream_of_available_space(self):
        self._set_waiting_for_part(True)
        super().notify_upstream_of_available_space()

    def space_available_downstream(self):
        '''Notify of available space downstream.

        Will schedule an attempt to pass a Part downstream but only if
        it was waiting for downstream space to become available.
        '''
        if self.is_operational() and self._waiting_for_downstream_space:
            self._schedule_pass_part_downstream()

    def give_part(self, part):
        if not self._can_accept_part(part):
            return False
        self._accept_part(part)
        return True

    def _can_accept_part(self, part):
        return super()._can_accept_part(part) and self._part == None and self._output == None

    def _accept_part(self, part):
        assert part != None, 'part cannot be None.'
        self._part = part
        self._part.add_routing_history(self)
        self._set_waiting_for_part(False)
        self._on_received_new_part()

    def _on_received_new_part(self):
        self._env.add_datapoint('received_part', self.name, (self._env.now,
                                                              self._part.id,
                                                              self._part.quality,
                                                              self._part.value))
        for c in self._received_part_callbacks:
            c(self, self._part)
        if self._output == None:
            self._try_move_part_to_output()

    def _try_move_part_to_output(self):
        if self.is_operational() and self._part != None and self._output == None:
            self._schedule_finish_cycle()

    def _schedule_finish_cycle(self, time_offset = 0):
        '''If the final cycle time <= 0 then _finish_cycle will be
        called immediately.
        '''
        next_cycle_time = max(0, self.cycle_time + self._next_cycle_time_offset + time_offset)
        self._next_cycle_time_offset = 0
        if next_cycle_time <= 0:
            self._finish_cycle()
        else:
            self._env.schedule_event(
                self._env.now + next_cycle_time,
                self.id,
                self._finish_cycle,
                EventType.FINISH_PROCESSING,
                f'By {self.name}'
            )

    def _finish_cycle(self):
        # If not operational then the events for this device should
        # have been paused or cancelled.
        assert self.is_operational(), 'Invalid PartHandler state.'
        assert self._part != None, f'Input part is missing.'
        assert self._output == None, f'Output part slot is already full.'

        self._output = self._part
        self._part = None
        self._schedule_pass_part_downstream()

    def _schedule_pass_part_downstream(self, time_offset = 0):
        self._waiting_for_downstream_space = False
        event_time = max(0, self._env.now + time_offset)
        self._env.schedule_event(event_time, self.id, self._pass_part_downstream,
                                 EventType.PASS_PART, f'From {self.name}')

    def _pass_part_downstream(self):
        if not self.is_operational() or self._output == None:
            return

        for dwn in self.get_sorted_downstream_list():
            if dwn.give_part(self._output):
                self._output = None
                self.notify_upstream_of_available_space()
                return
        # Could not pass part downstream
        self._waiting_for_downstream_space = True

    def _set_waiting_for_part(self, is_waiting = True, reset = False):
        if is_waiting == False:
            self._waiting_for_part_since = None
        else:
            if self._waiting_for_part_since != None and not reset:
                # Already waiting for a part.
                return
            elif self._env != None:
                self._waiting_for_part_since = self._env.now

    def add_receive_part_callback(self, callback):
        '''Register a function to be called when the PartHandler
        receives a new Part.

        | Callback signature: callback(part_handler, part)
        | part_handler - PartHandler that received the new Part.
        | part - Part that was received.

        If the cycle time is changed within this callback then the new
        cycle time will be used for the Part that triggered the
        callback. All future cycles would also use the new cycle time
        unless it is changed again.

        Arguments
        ---------
        callback: function
            Function to be called.
        '''
        assert_callable(callback)
        self._received_part_callbacks.append(callback)

