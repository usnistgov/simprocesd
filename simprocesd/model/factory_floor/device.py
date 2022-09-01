from ...utils.utils import assert_is_instance
from ..simulation import EventType
from .asset import Asset


class Device(Asset):
    ''' Base class for a production device. Contains the logic for
    handing parts in a production line.

    Arguments:
    name -- name of the device.
    upstream -- devices that can pass parts to this one.
    value -- starting value of the device.
    '''

    def __init__(self, name = None, upstream = [], value = 0):
        super().__init__(name, value)

        self._downstream = []
        self._upstream = []
        self._part = None
        self._output = None
        self._waiting_for_space_availability = False
        self._waiting_for_part_since = 0
        self._env = None

        self.set_upstream(upstream)

    def initialize(self, env):
        if self._env == None:
            # If this is the the first time initialize is called then
            # save the starting upstream list.
            self._initial_upstream = self.upstream
        else:
            # Simulation is resetting, restore starting upstream list.
            self.set_upstream(self._initial_upstream)

        super().initialize(env)
        self._part = None
        self._output = None
        self._waiting_for_space_availability = False
        self._waiting_for_part_since = self._env.now

    def is_operational(self):
        ''' Returns True is the device can perform its part handling
        and processing functions, returns False otherwise.
        '''
        return True

    @property
    def upstream(self):
        ''' List of upstream devices, devices that can provide parts
        to this one.
        '''
        return self._upstream.copy()

    def set_upstream(self, new_upstream_list):
        assert_is_instance(new_upstream_list, list)
        for up in self._upstream:
            up._remove_downstream(self)
        # Use a copy() of new_upstream_list in case it's modified later.
        self._upstream = new_upstream_list.copy()
        for up in self._upstream:
            assert_is_instance(up, Device)
            # This scenario is not supported.
            # Use an intermediate buffer or extend the class to do
            # multiple cycles without releasing the part.
            assert up != self, 'Device\'s upstream cannot point directly to itself.'
            up._add_downstream(self)
        # Reset waiting time if Device was already waiting for a part.
        if self.waiting_for_part_start_time != None:
            self._set_waiting_for_part(True, True)

    @property
    def downstream(self):
        ''' List of downstream devices, devices that receive parts from
        this one.

        The list is dependent on upstream and cannot be set or modified
        directly.
        '''
        return self._downstream.copy()

    @property
    def waiting_for_part_start_time(self):
        ''' Returns the simulation time of when this device started
        waiting for the next Part or returns None if the device is not
        currently waiting for a Part.
        Value is reset every time a new part is received.
        '''
        return self._waiting_for_part_since

    def _add_downstream(self, downstream):
        self._downstream.append(downstream)

    def _remove_downstream(self, downstream):
        self._downstream.remove(downstream)

    def _schedule_pass_part_downstream(self):
        self._waiting_for_space_availability = False
        self._env.schedule_event(self._env.now, self.id, self._pass_part_downstream,
                                 EventType.PASS_PART, f'From {self.name}')

    def _pass_part_downstream(self):
        if not self.is_operational() or self._output == None: return

        for dwn in self._priority_sorted_downstream():
            if dwn.give_part(self._output):
                self._output = None
                if self._part == None:
                    self.notify_upstream_of_available_space()
                return
        # Could not pass part downstream
        self._waiting_for_space_availability = True

    def _priority_sorted_downstream(self):
        return sorted(self._downstream, key = lambda d: d.waiting_for_part_start_time \
                      if d.waiting_for_part_start_time != None else float('inf'))

    def _set_waiting_for_part(self, is_waiting = True, reset = False):
        if is_waiting == False:
            self._waiting_for_part_since = None
        else:
            if self._waiting_for_part_since != None and not reset:
                # Device was already waiting for a part.
                return
            elif self._env != None:
                self._waiting_for_part_since = self._env.now

    def notify_upstream_of_available_space(self):
        ''' Communicate to all immediate upstream devices that this
        device can accept a new part.
        '''
        self._set_waiting_for_part(True)
        for up in self._upstream:
            up.space_available_downstream()

    def space_available_downstream(self):
        ''' Notify this device that downstream now can accept a part.
        This does not guarantee that this device will pass a part
        downstream because space could become unavailable before this
        device gets the chance to pass its part.
        '''
        if self.is_operational() and self._waiting_for_space_availability:
            self._schedule_pass_part_downstream()

    def give_part(self, part):
        ''' Try to pass a part to this device.
        Returns True if the part has been accepted, otherwise False.
        '''
        assert part != None, 'Cannot give part=None.'
        if not self.is_operational() or self._part != None or self._output != None:
            return False

        self._part = part
        self._part.routing_history.append(self)
        self._set_waiting_for_part(False)
        self._on_received_new_part()
        return True

    def _on_received_new_part(self):
        if self._output == None:
            self._try_move_part_to_output()

    def _try_move_part_to_output(self):
        if not self.is_operational() or self._part == None or self._output != None:
            return
        self._output = self._part
        self._part = None
        self._schedule_pass_part_downstream()
        return

