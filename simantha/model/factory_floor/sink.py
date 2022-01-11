from .machine_asset import MachineAsset


class Sink(MachineAsset):

    def __init__(self,
                 name = None,
                 time_to_receive_part = 0,
                 collect_parts = False,
                 **kwargs):
        super().__init__(name, cycle_time = time_to_receive_part, value = 0, **kwargs)

        self._collect_parts = collect_parts
        self.collected_parts = []
        self._received_parts_count = 0

    @property
    def received_parts_count(self):
        return self._received_parts_count

    @property
    def value_of_received_parts(self):
        return self.value

    def _get_part_from_upstream(self):
        super()._get_part_from_upstream()

        if self._part != None:
            self._received_parts_count += 1
            self.add_value(f'collected_part', self._part.value)
            if self._collect_parts:
                self.collected_parts.append(self._part)

    def _finish_processing_part(self):
        super()._finish_processing_part()
        self._output_part = None
        self._schedule_get_part_from_upstream()
