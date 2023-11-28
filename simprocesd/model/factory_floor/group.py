from ...utils.utils import assert_is_instance
from .part_flow_controller import PartFlowController


class Group():
    '''A grouping of devices for the purpose of using them in multiple
    production path locations.

    The first device in the device list will receive Parts that are
    passed to the group the group while Parts that leave the last
    device in the list will be routed out of the Group.
    Group will not interconnect the devices passed to it so upstreams
    need to be set independently (except for what is stated above).

    First device will also have its upstream set to GroupInput and
    last device will get a new downstream of GroupOutput.

    Once a group is created use get_new_group_path to create a new
    production line device. Parts that go into this GroupPath will be
    routed to a device in the group and once the Part leaves the group
    it will be routed back out of the same GroupPath.

    Arguments
    ---------
    group_name: str
        Name of the group.
    devices: list of PartFlowController
        List of devices that are part of this Group.

    Raises
    ------
    TypeError
        If any of the devices are not PartFlowController or a
        subclass of it.
    '''

    def __init__(self, group_name, devices):
        assert len(devices) > 0, 'There has to be at least 1 device in the group'
        self._devices = devices
        self.name = group_name
        self._group_paths = []

        for device in self._devices:
            assert_is_instance(device, PartFlowController)
            device._joined_groups.append(self)
            # Devices cannot be directly connected to devices outside
            # of the Group.
            for dwn in device.downstream:
                if dwn not in self._devices:
                    raise ValueError(f'Provided device, ({device.name}) has a downstream ({dwn.name})'
                                     +' that is not one of the other provided devices.')
            for up in device.upstream:
                if up not in self._devices:
                    raise ValueError(f'Provided device, ({device.name}) has an upstream ({up.name})'
                                     +' that is not one of the other provided devices.')

        self._input_device = GroupInput(self)
        self._output_device = GroupOutput(self)

    def get_new_group_path(self, name = None, upstream = None):
        '''Create a new GroupPath that acts like a device.

        The new GroupPath that will route the Parts it receives to the
        Group's Device(s) and when the Parts exit the Group they will
        exit from the same GrouPath they entered.

        Arguments
        ---------
        name: str, default=None
            Name of the GroupPath Asset that will be created. If name
            is None then a default name will be used:
            <class_name>_<asset_id>
        upstream: list of PartFlowController, default=None
            List of devices from which Parts can be received.
        '''
        return GroupPath(self, name, upstream)


class GroupInput(PartFlowController):

    def __init__(self, group):
        super().__init__()
        self._group = group
        self._joined_groups.append(self._group)

        first_device = group._devices[0]
        first_device.set_upstream([self])

    @property
    def upstream(self):
        all_upstreams = []
        for gp in self._group._group_paths:
            for u in gp.upstream:
                if u not in all_upstreams:
                    all_upstreams.append(u)
        return all_upstreams

    def give_part(self, part):
        return self._give_part_helper(part, False)

    def space_available_downstream(self):
        self.notify_upstream_of_available_space()

    def notify_upstream_of_available_space(self):
        # Will notify upstreams of all associated GroupPaths.
        for gp in self._group._group_paths:
            gp.notify_upstream_of_available_space()

    def set_upstream(self, new_upstream_list):
        if new_upstream_list != [] and new_upstream_list != None:
            raise ValueError('Source cannot have an upstream.')


class GroupOutput(PartFlowController):

    def __init__(self, group):
        super().__init__()
        self._group = group
        self._joined_groups.append(self._group)

        last_device = group._devices[-1]
        self.set_upstream([last_device])

    @property
    def downstream(self):
        all_downstreams = []
        for gp in self._group._group_paths:
            for d in gp.downstream:
                if d not in all_downstreams:
                    all_downstreams.extend(d)
        return all_downstreams

    def space_available_downstream(self):
        self.notify_upstream_of_available_space()

    def give_part(self, part):
        try:
            last_entered_group = part._group_pathing[-1]
        except IndexError:
            raise RuntimeError(f'Part {part.name} is trying to exit Group {self._group.name}'
                               +f' but does not contain information on which GroupPath to use.')

        did_pass = last_entered_group._pass_part_downstream(part)
        if did_pass:
            part._group_pathing.pop()
        return did_pass

    def _add_downstream(self, downstream):
        raise NotImplementedError()


class GroupPath(PartFlowController):
    '''See Group documentation for how GroupPath is used.

    Arguments
    ---------
    group: Group
        Group where Parts will go when routed to this GroupPath.
    name: str, default=None
        Name of the Asset. If name is None then a default name will be
        used: <class_name>_<asset_id>
    upstream: list of PartFlowController, default=None
        List of PartFlowControllers from which Parts can be received.

    '''

    def __init__(self, group, name = None, upstream = None):
        super().__init__(name, upstream)

        self._group = group
        self._group._group_paths.append(self)

    def space_available_downstream(self):
        self._group._output_device.space_available_downstream()

    def give_part(self, part):
        if self._block_input:
            return False

        part._group_pathing.append(self)
        part.add_routing_history(self)
        did_pass = self._group._input_device.give_part(part)
        if not did_pass:
            part._group_pathing.pop()
            part.remove_from_routing_history(-1)
        return did_pass

    def _pass_part_downstream(self, part):
        for dwn in self.get_sorted_downstream_list():
            if dwn.give_part(part):
                return True
        return False

