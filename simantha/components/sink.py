from .machine_asset import MachineAsset


class Sink(MachineAsset):

    def __init__(
        self, name = None,
        upstream = [],
        time_to_receive_part = 0,
        collect_parts = False
    ):
        super().__init__(name, upstream, cycle_time = time_to_receive_part)

        self._collect_parts = collect_parts
        self.collected_parts = []
        self._received_parts_count = 0

    @property
    def received_parts_count(self):
        return self._received_parts_count

    def _get_part_from_upstream(self):
        super()._get_part_from_upstream()
        if self._part != None:
            self._received_parts_count += 1
            if self._collect_parts:
                self.collected_parts.append(self._part)

    def _finish_processing_part(self):
        super()._finish_processing_part()
        self._output_part = None
