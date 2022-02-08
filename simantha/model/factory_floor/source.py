from ...utils import assert_is_instance
from .machine import Machine
from .part import Part


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

        self._output = self._sample_part.copy()
        self._output.initialize(self._env)
        self._output.routing_history.append(self.name)
        self.add_cost('supplied_part', self._output.value)
        self._produced_parts += 1
        self._schedule_pass_part_downstream()

    def _pass_part_downstream(self):
        super()._pass_part_downstream()
        if self._output == None:
            self._env.add_datapoint('supplied_new_part', self.name, self._env.now)
            self._prepare_next_part()

