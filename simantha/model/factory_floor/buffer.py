from .machine_asset import MachineAsset


class Buffer(MachineAsset):
    ''' Buffers store parts that are waiting for processing at a downstream machine.'''

    def __init__(self, name = None, capacity = float('inf'), **kwargs):
        assert int(capacity) >= 1, 'Capacity has to be at least 1.'
        super().__init__(name, cycle_time = 0, **kwargs)

        self._capacity = capacity
        self._buffer = []

    def _get_part_from_upstream(self):
        if len(self._buffer) < self._capacity:
            super()._get_part_from_upstream()

    def _finish_processing_part(self):
        super()._finish_processing_part()
        self._buffer.append(super()._take_part())

    def _take_part(self):
        if not self.is_operational or len(self._buffer) < 1:
            return None
        if len(self._buffer) == self._capacity:
            self._schedule_get_part_from_upstream()
        return self._buffer.pop(0)
