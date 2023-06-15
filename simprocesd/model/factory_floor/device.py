from ...utils.utils import assert_is_instance, assert_callable
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
    upstream: list, default=None
        A list of upstream Device objects.
    value: float, default=0
        Starting value of the Device.
    '''

    def __init__(self, name = None, upstream = None, value = 0):
        super().__init__(name, value)

        self._downstream = []
        self._upstream = []
        self._part = None
        self._output = None
        self._waiting_for_space_availability = False
        self._waiting_for_part_since = 0
        self._received_part_callbacks = []
        self._block_input = False

        if upstream == None:
            upstream = []
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

    @property
    def block_input(self):
        '''When set to True this Device will not accept new Parts from
        upstream.
        '''
        return self._block_input

    @block_input.setter
    def block_input(self, is_blocked):
        assert isinstance(is_blocked, bool)
        if self._block_input == is_blocked:
            return
        self._block_input = is_blocked
        if not is_blocked and self._output == None and self._part == None:
            self.notify_upstream_of_available_space()

    def _add_downstream(self, downstream):
        if downstream not in self._downstream:
            self._downstream.append(downstream)

    def _remove_downstream(self, downstream):
        self._downstream.remove(downstream)

    def _schedule_pass_part_downstream(self, delay = 0):
        self._waiting_for_space_availability = False
        self._env.schedule_event(self._env.now + delay, self.id, self._pass_part_downstream,
                                 EventType.PASS_PART, f'From {self.name}')

    def _pass_part_downstream(self):
        if not self.is_operational() or self._output == None: return

        for dwn in self.get_sorted_downstream_list():
            if dwn.give_part(self._output):
                self._output = None
                if self._part == None:
                    self.notify_upstream_of_available_space()
                else:
                    self._try_move_part_to_output()
                return
        # Could not pass part downstream
        self._waiting_for_space_availability = True

    def get_sorted_downstream_list(self):
        '''Get the sorted list of downstream Devices.

        Returns
        -------
        list
            A sorted list of downstream devices.
        '''
        return Device.downstream_priority_sorter(self.downstream)

    @staticmethod
    def downstream_priority_sorter(downstream):
        '''Sort the downstream list in a descending priority of where
        Parts should be moved to first.

        Default implementation gives higher priority to Devices that
        have been waiting for a Part the longest.

        Note
        ----
        Overwrite this static function to change how all Devices
        prioritize where Parts are passed.

        Arguments
        ---------
        downstream: list
            A list of downstream Devices.

        Returns
        -------
        list
            A list of downstream devices sorted from highest to lowest
            priority.
        '''
        return sorted(downstream, key = lambda d: d.waiting_for_part_start_time \
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
        if not self._can_accept_part(part):
            return False
        self._accept_part(part)
        return True

    def _can_accept_part(self, part):
        return (self.is_operational() and part != None
                                      and self._part == None
                                      and self._output == None
                                      and not self._block_input)

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
        if not self.is_operational() or self._part == None or self._output != None:
            return
        self._output = self._part
        self._part = None
        self._schedule_pass_part_downstream()
        return

    def add_receive_part_callback(self, callback):
        '''Setup a function to be called when the Machine receives a
        new Part.

        | Callback signature: callback(machine, part)
        | machine - Machine to which the callback was added.
        | part - Part that was lost or None if no Part was lost.

        If Machine cycle time is changed within the callback then it
        will be used as the processing time for the Part that was just
        received as well as all the future Parts.

        Arguments
        ---------
        callback: function
            Function to be called.
        '''
        assert_callable(callback)
        self._received_part_callbacks.append(callback)

