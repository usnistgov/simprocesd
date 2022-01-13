from .machine import Machine
from .part import Part
from ...utils import assert_is_instance


class Source(Machine):

    def __init__(self,
                 name = None,
                 # All sources share the default sample part.
                 sample_part = Part(),
                 time_to_produce_part = 0.0,
                 max_produced_parts = float('inf')):
        super().__init__(name, upstream = [self], cycle_time = time_to_produce_part,
                         value = 0)

        assert_is_instance(sample_part, Part)
        self._sample_part = sample_part

        self._max_produced_parts = max_produced_parts
        self._produced_parts = 0

    @property
    def cost_of_produced_parts(self):
        return -self.value

    @property
    def produced_parts(self):
        return self._produced_parts

    def _take_part(self):
        if not self._is_operational or self._produced_parts >= self._max_produced_parts:
            return None

        part = super()._take_part()
        if part != None:
            self.add_cost('supplied_part', part.value)
            self._produced_parts += 1
        return part

    def _get_part_from_upstream(self):
        if not self._is_operational: return
        self._part = self._sample_part.copy()
        self._part.initialize(self._env)
        self._on_received_new_part()

