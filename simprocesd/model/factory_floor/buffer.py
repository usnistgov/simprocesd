from .machine import Machine


class Buffer(Machine):
    '''A device that can store multiple parts.

    Buffer stores received Parts and can pass the stored Parts
    downstream. At any given time Buffer can store a number of Parts
    up to its storage capacity.

    Arguments
    ----------
    name : str, default=None
        Name of the Buffer. If name is None the Asset's name with be
        changed to Buffer_<id>
    upstream: list, default=[]
        A list of upstream Devices.
    cycle_time: float, default=0
        How long it takes to receive a Part.
    capacity: int, optional
        Maximum number of Parts that can be stored in the Buffer. No
        maximum if not set.
    value: float, default=0
        Starting value of the machine.
    '''

    def __init__(self, name = None, upstream = [], cycle_time = 0,
                 capacity = float('inf'), value = 0):
        assert int(capacity) >= 1, 'Capacity has to be at least 2.'
        super().__init__(name, upstream, cycle_time, value = value)

        self._capacity = capacity
        self._buffer = []

    def initialize(self, env):
        super().initialize(env)
        self._buffer = []

    def level(self):
        '''Returns
        -------
        int
            Number of Parts held by the buffer.
        '''
        return len(self._buffer) + (1 if self._part != None else 0)

    def _finish_processing_part(self):
        super()._finish_processing_part()
        if self._output:
            self._buffer.append(self._output)
            self._output = None
            self.notify_upstream_of_available_space()

    def notify_upstream_of_available_space(self):
        if self.level() < self._capacity:
            super().notify_upstream_of_available_space()

    def _pass_part_downstream(self):
        if not self.is_operational(): return

        # Try to pass parts to downstream machines.
        for dwn in self._priority_sorted_downstream():
            while len(self._buffer) > 0 and dwn.give_part(self._buffer[0]):
                self._buffer.pop(0)

        self.notify_upstream_of_available_space()
        if len(self._buffer) > 0:
            self._waiting_for_space_availability = True

    def give_part(self, part):
        if len(self._buffer) >= self._capacity:
            return False
        return super().give_part(part)
