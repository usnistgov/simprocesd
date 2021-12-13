from .machine_asset import MachineAsset


class Buffer(MachineAsset):
    """ Buffers store parts that are waiting for processing at a downstream machine."""

    def __init__(self, name = None, capacity = float('inf'), **kwargs):
        assert int(capacity) > 0, "Capacity can't be less than 1."
        super().__init__(name, cycle_time = 0, **kwargs)

        self._capacity = capacity
        self._buffer = []

    def _start_processing_part(self):
        if not self._is_operational: return
        assert self._part != None, "Bad state, part should be available."

        if self._output_part != None:
            self._waiting_for_output_availability = True
        else:
            self.machine_status.start_processing(self._part)
            self._schedule_finish_processing_part()

    def _finish_processing_part(self):
        super()._finish_processing_part()

        if len(self._buffer) < self._capacity - 1:  # -1 to account for item in self._part
            self._buffer.append(self._output_part)
            self._output_part = None

    def _take_part(self):
        if not self.is_operational: return

        if len(self._buffer) < 1:
            return None

        temp = self._buffer.pop(0)
        if self._output_part != None:
            self._buffer.append(self._output_part)
            self._output_part = None
            if self._waiting_for_output_availability:
                self._schedule_start_processing_part()
        return temp
