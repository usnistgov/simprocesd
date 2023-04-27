import math

from .machine import Device


class Buffer(Device):
    '''A device that can store multiple parts.

    Buffer stores received Parts and can pass the stored Parts
    downstream. At any given time Buffer can store a number of Parts
    up to its storage capacity.

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
        super().__init__(name, upstream, value)

        self._minimum_delay = minimum_delay
        if capacity == None:
            self._capacity = float('inf')
        else:
            self._capacity = math.floor(capacity)
        assert self._capacity >= 1, 'Capacity has to be at least 1.'
        self._buffer = []

    def initialize(self, env):
        super().initialize(env)
        self._buffer = []

    @property
    def stored_parts(self):
        '''List of Parts currently stored in the Buffer.
        '''
        return [x[1] for x in self._buffer]

    def level(self):
        '''Returns
        -------
        int
            Number of Parts currently stored in the Buffer.
        '''
        return len(self._buffer) + (1 if self._part != None else 0)

    def _can_accept_part(self, part):
        if len(self._buffer) >= self._capacity:
            return False
        else:
            return super()._can_accept_part(part)

    def _try_move_part_to_output(self):
        if not self.is_operational(): return

        if self._part:
            self._buffer.append((self.env.now, self._part))
            self._part = None
            self.notify_upstream_of_available_space()
            if len(self._buffer) == 1:
                self._schedule_pass_part_downstream(delay = self._minimum_delay)

    def notify_upstream_of_available_space(self):
        if self.level() < self._capacity:
            super().notify_upstream_of_available_space()

    def _pass_part_downstream(self):
        i = 0
        while i < len(self._buffer):
            if self._buffer[i][0] > self.env.now - self._minimum_delay:
                # Not enough time passed for this Part.
                break
            for dwn in self.get_sorted_downstream_list():
                if dwn.give_part(self._buffer[i][1]):
                    self._buffer.pop(i)
                    i -= 1
                    break
            i += 1

        if len(self._buffer) > 0:
            # Only check first Part because later items guaranteed to
            # have arrived at the same time or later.
            time_passed = self.env.now - self._buffer[0][0]
            if time_passed < self._minimum_delay:
                self._schedule_pass_part_downstream(delay = self._minimum_delay - time_passed)
            else:
                self._waiting_for_space_availability = True
        self.notify_upstream_of_available_space()
