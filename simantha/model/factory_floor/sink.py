from .machine import Machine


class Sink(Machine):

    def __init__(self,
                 name = None,
                 upstream = [],
                 time_to_receive_part = 0,
                 collect_parts = False):
        super().__init__(name, upstream, cycle_time = time_to_receive_part, value = 0)

        self._collect_parts = collect_parts
        self.collected_parts = []
        self._received_parts_count = 0

    @property
    def received_parts_count(self):
        return self._received_parts_count

    @property
    def value_of_received_parts(self):
        return self.value

    def _on_received_new_part(self):
        self._received_parts_count += 1
        self.add_value(f'collected_part', self._part.value)
        self._env.add_datapoint('collected_part', self.name,
                                (self._env.now, self._part.quality, self._part.value))
        if self._collect_parts:
            self.collected_parts.append(self._part)

        super()._on_received_new_part()

    def _finish_processing_part(self):
        super()._finish_processing_part()
        if self._output == None: return

        self._output = None

    def _schedule_pass_part_downstream(self):
        pass  # Sink does not pass parts anywhere.

