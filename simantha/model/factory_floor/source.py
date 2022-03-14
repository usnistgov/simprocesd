from . import Machine, Part
from .. import EventType
from ...utils import assert_is_instance


class Source(Machine):
    ''' A machine that produces copies of Parts for the simulation.
    Source will not start producing next part until previous part is
    passed downstream.

    Arguments:
    name -- machine name.
    sample_part -- part which will be used to make copies. This part is
        never passed downstream, only copies of it will be passed.
    time_to_produce_part -- how long it takes to produce a part.
    max_produced_parts -- maximum number of parts to produce.
    '''

    def __init__(self, name = None, sample_part = None, time_to_produce_part = 0.0,
                 max_produced_parts = float('inf')):
        super().__init__(name, [], time_to_produce_part, value = 0)

        if sample_part == None:
            sample_part = Part()
        else:
            assert_is_instance(sample_part, Part)
        self._sample_part = sample_part

        self._max_produced_parts = max_produced_parts
        self._cost_of_produced_parts = 0
        self._produced_parts = 0

    @property
    def upstream(self):
        return self._upstream

    @upstream.setter
    def upstream(self, upstream):
        if upstream != []:
            raise AttributeError('Source cannot have an upstream.')

    @property
    def cost_of_produced_parts(self):
        ''' Returns the total value of parts that have been produced by
        this Source and passed downstream.
        '''
        return self._cost_of_produced_parts

    @property
    def produced_parts(self):
        ''' Returns the number of parts that have been produced by this
        Source and passed downstream.
        '''
        return self._produced_parts

    def initialize(self, env):
        super().initialize(env)
        self._schedule_prepare_next_part()

    def _schedule_prepare_next_part(self):
        self._env.schedule_event(
            self._env.now + self._cycle_time,
            self.id,
            self._prepare_next_part,
            EventType.FINISH_PROCESSING,
            f'By {self.name}'
        )

    def _prepare_next_part(self):
        if self._produced_parts >= self._max_produced_parts: return

        self._output = self._sample_part.copy()
        self._output.initialize(self._env)
        self._output.routing_history.append(self.name)
        self._schedule_pass_part_downstream()

    def _pass_part_downstream(self):
        output_before = self._output
        super()._pass_part_downstream()
        if self._output == None:
            self._env.add_datapoint('supplied_new_part', self.name, self._env.now)
            self._schedule_prepare_next_part()
            if output_before != None:
                # Part was passed downstream.
                self._cost_of_produced_parts += output_before.value
                self._produced_parts += 1
                self.add_cost('supplied_part', output_before.value)

