from ...utils.utils import assert_is_instance
from .asset import Asset


class PartFlowController(Asset):
    '''Base production line device.

    Passes Parts from upstream to downstream without buffering any
    Parts or any delays in time.

    Arguments
    ---------
    name: str, default=None
        Name of the Asset. If name is None then a default name will be
        used: <class_name>_<asset_id>
    upstream: list of PartFlowController, default=None
        List of devices from which Parts can be received.
    value: float, default=0
        Starting value of the Asset.
    '''

    def __init__(self, name = None, upstream = None, value = 0):
        self._downstream = []
        self._upstream = []
        self._block_input = False
        self._recursion_prevention = False
        self._joined_groups = []

        super().__init__(name, value)
        self.set_upstream(upstream)

    def is_operational(self):
        '''Check whether the PartFlowController is operational.

        Returns
        -------
        bool
            True if part handling and processing can currently be
            performed, otherwise False.
        '''
        return True

    @property
    def upstream(self):
        '''List of upstream PartFlowControllers.

        Can be changed using set_upstream(new_upstream).
        '''
        return self._upstream.copy()

    @property
    def downstream(self):
        '''List of downstream PartFlowControllers.

        This list shouldn't be set or modified directly because it's
        dependent on upstream settings of other PartFlowControllers.
        '''
        return self._downstream

    @property
    def waiting_for_part_start_time(self):
        '''Simulation time of when this device started waiting for the
        next Part. Is None if not currently waiting for a Part.

        Because PartFlowController does not hold Parts it instead
        looks at the immediate downstream devices and returns the
        earliest waiting_for_part_start_time from them.
        '''
        if self._recursion_prevention:
            return None
        self._recursion_prevention = True

        min_wait_start = float('inf')
        for d in self._downstream:
            if d.waiting_for_part_start_time != None:
                min_wait_start = min(min_wait_start, d.waiting_for_part_start_time)

        self._recursion_prevention = False
        return min_wait_start if min_wait_start != float('inf') else None

    @property
    def block_input(self):
        '''When set to True this PartFlowController will not accept
        new Parts.
        '''
        return self._block_input

    @block_input.setter
    def block_input(self, is_blocked):
        assert isinstance(is_blocked, bool)
        if self._block_input == is_blocked:
            return
        self._block_input = is_blocked
        if not is_blocked:
            self.notify_upstream_of_available_space()

    @property
    def joined_groups(self):
        '''List of Groups that this PartFlowController is a part of.
        '''
        return self._joined_groups.copy()

    def set_upstream(self, new_upstream):
        '''Replace a set of upstream PartFlowControllers.

        Arguments
        ---------
        new_upstream: list of PartFlowController
            PartFlowControllers that will replace the current
            collection of upstreams.
            If None, then an empty list will be used.

        Raises
        ------
        TypeError
            If an object in the list is not a PartFlowController or a
            child of that class.
        AssertionError
            If an element in new_upstream includes itself.
        '''
        if new_upstream == None:
            new_upstream = []
        else:
            assert_is_instance(new_upstream, list)
        # Verify that the new upstreams are valid.
        for up in new_upstream:
            assert_is_instance(up, PartFlowController)
            # This scenario is not supported.
            # Use an intermediate buffer or extend the class to do
            # multiple cycles without releasing the Part.
            assert up != self, 'Upstream cannot include itself.'
            if set(up.joined_groups) != set(self._joined_groups):
                raise RuntimeError('Upsteam is not a member of the same groups.'
                                   +f' {self.name}: {self._joined_groups} | {up.name}: {up.joined_groups}')

        for up in self._upstream:
            up._remove_downstream(self)
        self._upstream = new_upstream.copy()
        for up in self._upstream:
            up._add_downstream(self)

    def _add_downstream(self, downstream):
        if downstream not in self._downstream:
            self._downstream.append(downstream)
            if self.env != None:
                self.space_available_downstream()

    def _remove_downstream(self, downstream):
        self._downstream.remove(downstream)

    def get_sorted_downstream_list(self):
        '''Get the sorted list of downstream PartFlowControllers.

        Returns
        -------
        list
            A sorted list of downstream PartFlowControllers.
        '''
        return PartFlowController.downstream_priority_sorter(self._downstream)

    @staticmethod
    def downstream_priority_sorter(downstream):
        '''Sort the downstream list in a descending priority of where
        Parts should be passed to first.

        Default implementation gives higher priority to downstreams
        that have been waiting for a Part the longest.

        Note
        ----
        Overwrite this static function to change how all
        PartFlowControllers prioritize where Parts are passed.

        Arguments
        ---------
        downstream: list
            A list of downstream PartFlowControllers.

        Returns
        -------
        list
            A sorted list of downstream PartFlowControllers sorted
            from highest to lowest priority.
        '''
        return sorted(downstream, key = PartFlowController._downstream_sorting_key_generator)

    @staticmethod
    def _downstream_sorting_key_generator(downstream):
        if downstream.waiting_for_part_start_time == None:
            return float('inf')
        return downstream.waiting_for_part_start_time

    def notify_upstream_of_available_space(self):
        '''Communicate to all immediate upstreams that this
        PartFlowController can accept a new Part.

        Should be called automatically when space for a Part becomes
        available.
        '''
        for up in self._upstream:
            up.space_available_downstream()

    def space_available_downstream(self):
        '''Notify of available space downstream.

        Will attempt to pass a Part downstream if a ready Part is
        available.
        '''
        if self.is_operational():
            self.notify_upstream_of_available_space()

    def give_part(self, part):
        '''Try to pass a Part to this PartFlowController.

        Arguments
        ---------
        part: Part
            Part that is being passed.

        Returns
        -------
        bool
            True if the Part has been accepted, otherwise False.
        '''
        return self._give_part_helper(part, True)

    def _give_part_helper(self, part, add_routing_history):
        if not self._can_accept_part(part):
            return False

        if add_routing_history:
            # Add routing history in case the part is successfully
            # passed through.
            part.add_routing_history(self)

        for dwn in self.get_sorted_downstream_list():
            if dwn.give_part(part):
                return True

        if add_routing_history:
            # Part was never passed and remains in an upstream device.
            part.remove_from_routing_history(-1)
        return False

    def _can_accept_part(self, part):
        return self.is_operational() and part != None and not self._block_input

