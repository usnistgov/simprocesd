from . import Machine, Part
from .. import EventType
from ...utils import assert_is_instance


class Source(Machine):
    '''A Device that produces Part objects and supplies them to Devices
    downstream. It is the start of a production line.

    Source will not start producing a next Part until previous Part is
    passed downstream.

    Note
    ----
    Source value will decrease by sample_part.value every time a new
    Part is created. This is how Source tracks the costs of producing
    Parts.

    Arguments
    ----------
    name: str, default=None
        Name of the Source. If name is None then the Source's name will
        be changed to Source_<id>
    sample_part: Part, default=None
        Source will produce copies of this Part and pass them
        downstream, sample_part itself is never passed.
        If sample_part is None then it will be set to Part()
    cycle_time: float, default=0
        How long it takes to produce a Part.
    max_produced_parts: int, optional
        Maximum number of Parts to produce. No maximum if not set.
    '''

    def __init__(self, name = None, sample_part = None, cycle_time = 0.0,
                 max_produced_parts = float('inf')):
        super().__init__(name, [], cycle_time, value = 0)

        if sample_part == None:
            sample_part = Part()
        else:
            assert_is_instance(sample_part, Part)
        self._sample_part = sample_part

        self._max_produced_parts = max_produced_parts
        self._cost_of_produced_parts = 0
        self._produced_parts = 0

    def initialize(self, env):
        super().initialize(env)
        self._sample_part.initialize(env)
        self._cost_of_produced_parts = 0
        self._produced_parts = 0

        self._schedule_prepare_next_part()

    def set_upstream(self, new_upstream_list):
        ''' Source cannot have upstream Devices.

        Raises
        ------
        ValueError
            if new_upstream_list is not an empty list.
        '''
        if new_upstream_list != []:
            raise ValueError('Source cannot have an upstream.')

    @property
    def cost_of_produced_parts(self):
        ''' Returns the summed value of the parts that have been
        produced by this Source and passed downstream.
        '''
        return self._cost_of_produced_parts

    @property
    def produced_parts(self):
        ''' Returns the count of the parts that have been produced by
        this Source and passed downstream.
        '''
        return self._produced_parts

    def _schedule_prepare_next_part(self):
        self._env.schedule_event(
            self._env.now + self._cycle_time,
            self.id,
            self._prepare_next_part,
            EventType.FINISH_PROCESSING,
            f'By {self.name}'
        )

    def _prepare_next_part(self):
        self._output = self._sample_part.make_copy()
        self._output.initialize(self._env)
        self._output.routing_history.append(self)

        self._schedule_pass_part_downstream()

    def _pass_part_downstream(self):
        if self._produced_parts + 1 > self._max_produced_parts: return

        output_before = self._output
        super()._pass_part_downstream()
        if output_before != None and self._output == None:
            self._produced_parts += 1
            self.add_cost('supplied_part', output_before.value)
            self._cost_of_produced_parts += output_before.value
            self._env.add_datapoint('supplied_new_part', self.name, (self._env.now,))
            self._schedule_prepare_next_part()

