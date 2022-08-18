from .machine import Machine


class Buffer(Machine):
    ''' A Buffer can store parts from upstream and pass them downstream
    in the order they were received.

    Arguments:
    name -- name of the Buffer.
    upstream -- list of upstream devices.
    cycle_time -- how long it takes for a part to be received before
        it can be passed downstream.
    capacity -- maximum number of parts that can be stored in the Buffer
        at once.
    value -- starting value of the Buffer.
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
        ''' Return how many parts are currently held by the buffer.
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
