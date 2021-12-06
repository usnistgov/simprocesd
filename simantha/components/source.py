from .machine_asset import MachineAsset
from .part import Part
from ..utils import assert_is_instance


class Source(MachineAsset):

    def __init__(self,
                 name = None,
                 sample_part = Part(),
                 time_to_produce_part = 0.0,
                 max_produced_parts = float('inf'),
                 **kwargs):
        super().__init__(name, upstream = [self], cycle_time = time_to_produce_part,
                         **kwargs)

        assert_is_instance(sample_part, Part)
        self._sample_part = sample_part

        self._cost_of_produced_parts = 0
        self._max_produced_parts = max_produced_parts
        self._produced_parts = 0

    @property
    def cost_of_produced_parts(self):
        return self._cost_of_produced_parts

    @property
    def produced_parts(self):
        return self._produced_parts

    def _take_part(self):
        if not self._is_operational or self._produced_parts >= self._max_produced_parts:
            return
        self._cost_of_produced_parts += self._sample_part.value
        self._produced_parts += 1

        return super()._take_part()

    def _get_part_from_upstream(self):
        if not self._is_operational: return
        self._part = self._sample_part.copy()
        self._schedule_start_processing_part()

