from ...utils.utils import assert_is_instance
from ..simulation import EventType
from .asset import Asset


class Device(Asset):
    ''' Base class for production devices.

    Contains common logic for handling parts as they pass between
    Devices.

    Arguments
    ---------
    name: str, default=None
        Name of the Device. If name is None then the Device's name will
        be changed to Device_<id>
    upstream: list, default=[]
        A list of upstream Device objects.
    value: float, default=0
        Starting value of the Device.
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
        '''Check whether the Device is operational.

        Returns
        -------
        bool
            True is the Device can perform part handling and
            processing functions, otherwise False.
        '''
        return True

    @property
    def upstream(self):
        ''' List of upstream Devices, Devices that can feed Parts to
        this Device.

        Can be changed using set_upstream(new_list).
        '''
        return self._upstream.copy()

    def set_upstream(self, new_upstream_list):
        '''Replace a set of upstream Devices with a new one.

        Arguments
        ---------
        new_upstream_list: list
            List of Devices that will replace the previous set of
            upstream Devices.

        Raises
        ------
        TypeError
            If an object in the list is not a Device and does not extend
            the Device class.

        Warning
        -------
        A device cannot have itself as the upstream.
        '''
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
        ''' List of downstream Devices, Devices that can receive Parts
        from this Device.

        This list should not be set or modified directly because it's
        dependent on upstream settings of other Devices.
        '''
        return self._downstream.copy()

    @property
    def waiting_for_part_start_time(self):
        '''Simulation time of when this device started waiting for the
        next Part. Is set to None if the device is not currently waiting
        for a Part.
        '''
        return self._waiting_for_part_since

    def _add_downstream(self, downstream):
        if downstream not in self._downstream:
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
        ''' Communicate to all immediate upstream Devices that this
        Device can accept a new Part.

        If upstream Devices have a Part waiting to be passed they will
        try to do so in a separate Event scheduled for the current
        simulation time.
        '''
        self._set_waiting_for_part(True)
        for up in self._upstream:
            up.space_available_downstream()

    def space_available_downstream(self):
        ''' Notify this Device that downstream now can accept a Part.

        This does not guarantee that this Device will pass a Part
        downstream because space could become unavailable before this
        Device gets the chance to pass its Part.
        '''
        if self.is_operational() and self._waiting_for_space_availability:
            self._schedule_pass_part_downstream()

    def give_part(self, part):
        '''Try to pass a Part to this Device.

        Arguments
        ---------
        part: Part
            Part that is being passed.

        Returns
        -------
        bool
            True if the Part has been accepted, otherwise False.
        '''
        assert part != None, 'part should never be None.'
        if (not self.is_operational() or part == None
                                      or self._part != None
                                      or self._output != None):
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

