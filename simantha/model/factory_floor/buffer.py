from .machine import Machine


class Buffer(Machine):
    ''' Buffers store parts that are waiting for processing at a downstream machine.
    '''

    def __init__(self, name = None, upstream = [], time_to_receive_part = 0,
                 capacity = float('inf'), value = 0):
        assert int(capacity) >= 1, 'Capacity has to be at least 1.'
        super().__init__(name, upstream, time_to_receive_part, value = value)

        self._capacity = capacity
        self._buffer = []

    def _finish_processing_part(self):
        super()._finish_processing_part()
        if self._output:
            self._buffer.append(self._output)
            self._output = None

    def _notify_upstream_of_available_space(self):
        parts_count = (len(self._buffer) + 1 if self._part != None else 0
                                         +1 if self._output != None else 0)
        if parts_count < self._capacity:
            super()._notify_upstream_of_available_space()

    def _pass_part_downstream(self):
        if not self.is_operational: return

        # Try to pass parts to downstream machines.
        for dwn in self._downstream:
            while len(self._buffer) > 0 and dwn._give_part(self._buffer[0]):
                self._buffer.pop(0)

        self._notify_upstream_of_available_space()
        if len(self._buffer) > 0:
            self._waiting_for_space_availability = True

    def _give_part(self, part):
        if len(self._buffer) >= self._capacity:
            return False
        return super()._give_part(part)
