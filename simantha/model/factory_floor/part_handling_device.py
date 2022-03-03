from enum import Enum, auto, unique
import random

from ...utils.utils import assert_is_instance
from .machine_base import MachineBase


@unique
class FlowOrder(Enum):
    ''' Each attempt tries to pass a part to machines in downstream
    starting from first machine in the list and following list order,
    once end of list is reached the order jumps back to the beginning
    of the list.
    '''
    ROUND_ROBIN = auto()

    ''' Each attempt tries to pass a part to downstream machines in list
    order until a downstream machine accepts the part or end of list is
    reached.
    '''
    FIRST_AVAILABLE = auto()

    ''' Each attempt tries to pass a part to machines in downstream list
    in a random order until a downstream accepts the part or all
    downstream machines have been tried.
    Recommended to use set_downstream method to ensure correct list
    order of downstream machines.
    '''
    RANDOM = auto()


class PartHandlingDevice(MachineBase):
    ''' Accepts parts from upstream and sends them to downstream
    machines based on chosen order. If a part cannot be passed
    downstream then a part will not be accepted from upstream.

    Downstream order of the list will be used to determine order
    of which downstream machines get parts in what order. Downstream
    has to contain all and only of those MachineBase objects that have
    this PartHandlingDevice object as an upstream.
    '''

    def __init__(self,
                 name = None,
                 upstream = [],
                 flow_order = FlowOrder.ROUND_ROBIN):
        super().__init__(name, upstream, 0)

        self._try_pass_part = {FlowOrder.ROUND_ROBIN: self._try_pass_part_round_robin,
                               FlowOrder.FIRST_AVAILABLE: self._try_pass_part_first_available,
                               FlowOrder.RANDOM: self._try_pass_part_random
                              }[flow_order]
        self._next_round_robin_index = 0
        self._is_downstream_list_locked = False

    def set_downstream(self, downstream):
        ''' Sets downstream list to new value and locks the list from
        changing by means other than this function.
        '''
        assert_is_instance(downstream, list)
        self._is_downstream_list_locked = True
        self._downstream = downstream

    def _add_downstream(self, downstream):
        if not self._is_downstream_list_locked:
            super()._add_downstream(downstream)

    def _remove_downstream(self, downstream):
        if not self._is_downstream_list_locked:
            self._remove_downstream(downstream)

    def _try_pass_part_round_robin(self, part):
        starting_index = self._next_round_robin_index
        length = len(self._downstream)
        while part != None:
            if self._downstream[self._next_round_robin_index].give_part(part):
                part = None
            # Update next index
            self._next_round_robin_index = (self._next_round_robin_index + 1) % length
            if starting_index == self._next_round_robin_index:
                # All machines have been tried
                break
        return part == None

    def _try_pass_part_first_available(self, part):
        for dwn in self._downstream:
            if dwn.give_part(part):
                return True
        return False

    def _try_pass_part_random(self, part):
        downstream_copy = self._downstream.copy()
        random.shuffle(downstream_copy)
        while len(downstream_copy) > 0:
            if downstream_copy[0].give_part(part):
                return True
            else:
                downstream_copy.pop(0)
        return False

    def give_part(self, part):
        assert part != None, 'Part cannot be set to None.'
        if not self.is_operational():
            return False

        return self._try_pass_part(part)

    def space_available_downstream(self):
        if self.is_operational():
            self.notify_upstream_of_available_space()

    def _pass_part_downstream(self, part):
        # Safety check, function should never be called.
        raise RuntimeError('This method should never be called.')

