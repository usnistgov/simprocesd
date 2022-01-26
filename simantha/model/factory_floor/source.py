from .machine import Machine
from .part import Part
from ...utils import assert_is_instance


class Source(Machine):

    def __init__(self,
                 name = None,
                 # All sources share the default sample part.
                 sample_part = None,
                 time_to_produce_part = 0.0,
                 max_produced_parts = float('inf')):
        super().__init__(name, [], time_to_produce_part, value = 0)

        if sample_part == None:
            sample_part = Part()
        else:
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

    def initialize(self, env):
        super().initialize(env)
        self._prepare_next_part()

    def _prepare_next_part(self):
        if self._produced_parts >= self._max_produced_parts: return

        self._part = self._sample_part.copy()
        self._part.initialize(self._env)
        self.add_cost('supplied_part', self._part.value)
        self._produced_parts += 1
        self._on_received_new_part(self._part)

    def _pass_part_downstream(self):
        super()._pass_part_downstream()
        if self._part == None:
            self._prepare_next_part()

