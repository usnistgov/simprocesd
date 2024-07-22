import math
import numpy as np

from .part_handler import PartHandler
from .batch import Batch


class Buffer(PartHandler):
    '''A device that can store multiple parts.

    Buffer stores received Parts and can pass the stored Parts
    downstream. At any given time Buffer can store a number of Parts
    up to its storage capacity.

    Parts in the Buffer can only pass downstream in the order they were
    received.

    Arguments
    ----------
    name : str, default=None
        Name of the Buffer. If name is None the Asset's name with be
        changed to Buffer_<id>
    upstream: list, default=None
        A list of upstream Devices.
    minimum_delay: float, default=0
        Minimum time between any one Part being passed to the Buffer
        and that same Part being passed to downstream Devices.
    capacity: int, optional
        Maximum number of Parts that can be stored in the Buffer. No
        maximum if not set.
    value: float, default=0
        Starting value of the machine.
    '''

    def __init__(self, name = None, upstream = None, minimum_delay = 0,
                 capacity = None, value = 0):
        super().__init__(name, upstream, 0, value)

        self._minimum_delay = minimum_delay
        if capacity == None:
            self._capacity = float('inf')
        else:
            self._capacity = math.floor(capacity)
        assert self._capacity >= 1, 'Capacity has to be at least 1.'
        self._buffer = []
        self._level = 0

    @PartHandler.cycle_time.getter
    def cycle_time(self):
        '''Cycle time is not used by the buffer.
        '''
        return 0

    @property
    def stored_parts(self):
        '''List of Parts currently stored in the Buffer.
        '''
        return [x[1] for x in self._buffer]

    @property
    def capacity(self):
        '''Maximum number of Parts that can be stored in the Buffer.
        '''
        return self._capacity

    @property
    def minimum_delay(self):
        '''Minimum time between any one Part being passed to the Buffer
        and that same Part being passed to downstream Devices
        '''
        return self._minimum_delay

    def level(self):
        '''Returns
        -------
        int
            Number of Parts currently stored in the Buffer. Each Part
            within a Batch counts as a separate Part.
        '''
        return self._level

    def _can_accept_part(self, part):
        part_count = Buffer._get_part_count(part)
        if self.level() + part_count > self._capacity:
            return False
        else:
            return super()._can_accept_part(part)

    def _on_received_new_part(self):
        self._level += Buffer._get_part_count(self._part)
        self._env.add_datapoint('level', self.name, (self._env.now, self.level()))
        super()._on_received_new_part()

    def _try_move_part_to_output(self):
        if not self.is_operational() and self._part != None:
            return

        self._buffer.append((self.env.now, self._part))
        self._part = None
        self.notify_upstream_of_available_space()
        if len(self._buffer) == 1:
            # Indicates that the buffer was empty.
            self._schedule_pass_part_downstream(self._minimum_delay)

    def notify_upstream_of_available_space(self):
        if self.level() < self._capacity:
            super().notify_upstream_of_available_space()

    def _remaining_wait_time(self, stored_time):
        return self._minimum_delay - (self.env.now - stored_time)

    def _pass_part_downstream(self):
        # Use least significant bit of time instead of 0 to account for
        # rounding errors.
        min_time_change = np.nextafter(self.env.now, np.inf) - self.env.now

        can_continue = True
        while len(self._buffer) > 0 and can_continue:
            if self._remaining_wait_time(self._buffer[0][0]) > min_time_change:
                break
            can_continue = False
            for dwn in self.get_sorted_downstream_list():
                part_count = Buffer._get_part_count(self._buffer[0][1])
                if dwn.give_part(self._buffer[0][1]):
                    self._level -= part_count
                    self._buffer.pop(0)
                    self._env.add_datapoint('level', self.name, (self._env.now, self.level()))
                    can_continue = True
                    break

        if len(self._buffer) > 0:
            # Only check first Part because later items guaranteed to
            # have arrived at the same time or later.
            remaining_wait = self._remaining_wait_time(self._buffer[0][0])
            if remaining_wait > min_time_change:
                self._schedule_pass_part_downstream(time_offset = remaining_wait)
            else:
                self._waiting_for_downstream_space = True
        self.notify_upstream_of_available_space()

    @staticmethod
    def _get_part_count(part):
        if isinstance(part, Batch):
            return len(part.parts)
        else:
            return 1

