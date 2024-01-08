from ...utils import assert_is_instance
from .part_handler import PartHandler
from .part import PartGenerator


class Source(PartHandler):
    '''A device that produces Part objects and supplies them to
    devices downstream. It is the start of a production line.

    Source will not start producing next Part until previous Part is
    passed downstream.

    Note
    ----
    Source value will decrease by the value of every Part that is
    passed downstream. This is how Source tracks the costs of
    producing Parts.

    Arguments
    ----------
    name: str, default=None
        Name of the Asset. If name is None then a default name will be
        used: <class_name>_<asset_id>
    part_generator: PartGenerator, default=None
        Factory for generating Parts that the Source will supply.
        If None then the a default PartGenerator() will be used.
    cycle_time: float, default=0
        How long it takes to produce a Part.
    starting_parts: int, optional
        Number of available Parts to supply to downstream. Infinite if
        not set.
    '''

    def __init__(self, name = None, part_generator = None, cycle_time = 0.0,
                 starting_parts = float('inf')):
        super().__init__(name, None, cycle_time, value = 0)

        if part_generator == None:
            self._part_generator = PartGenerator(name_prefix = f'Part_{self.id}')
        else:
            assert_is_instance(part_generator, PartGenerator)
            self._part_generator = part_generator

        self._max_produced_parts = starting_parts
        self._cost_of_produced_parts = 0
        self._produced_parts = 0

    def initialize(self, env):
        super().initialize(env)
        self._schedule_finish_cycle()

    def set_upstream(self, new_upstream_list):
        '''Source cannot have upstream Devices.

        Raises
        ------
        ValueError
            if new_upstream_list is not an empty list.
        '''
        if new_upstream_list != [] and new_upstream_list != None:
            raise ValueError('Source cannot have an upstream.')

    @property
    def cost_of_produced_parts(self):
        '''Returns the summed value of the parts that have been
        produced by this Source and passed downstream.
        '''
        return self._cost_of_produced_parts

    @property
    def produced_parts(self):
        '''Returns the count of the parts that have been produced by
        this Source and passed downstream.
        '''
        return self._produced_parts

    @property
    def remaining_parts(self):
        '''How many Parts parts are left to be produced.
        '''
        return max(self._max_produced_parts - self._produced_parts, 0)

    def _finish_cycle(self):
        if self._output == None:
            self._output = self._part_generator.generate_part()
            self._output.initialize(self._env)
            self._output.add_routing_history(self)

        self._schedule_pass_part_downstream()

    def _pass_part_downstream(self):
        if self.remaining_parts < 1 or self._output == None:
            return
        supplied_part_value = self._output.value
        supplied_part_id = self._output.id
        super()._pass_part_downstream()
        if self._output == None:  # Part was passed downstream.
            self._produced_parts += 1
            self.add_cost('supplied_part', supplied_part_value)
            self._cost_of_produced_parts += supplied_part_value
            self._env.add_datapoint('supplied_new_part', self.name, (self._env.now, supplied_part_id))
            self._schedule_finish_cycle()

    def adjust_part_count(self, value):
        '''Update the number of remaining Parts.

        Increase or decrease the number of Parts this Source can
        supply/produce. Cannot decrease by more than the remaining
        Parts count.

        Arguments
        ---------
        value: int
            Number by which to adjust the remaining Parts count. If
            positive then the count will be increased, otherwise the
            count will be decreased.
            Remaining Parts count will never be decreased below 0.
        '''
        assert_is_instance(value, int)
        was_empty = self._max_produced_parts - self._produced_parts < 1
        # Maximum parts to produce can't be lower than produced parts.
        self._max_produced_parts = max(self._max_produced_parts + value, self._produced_parts)
        if was_empty:
            self._schedule_pass_part_downstream()

