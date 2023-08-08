import math

from ...utils import assert_is_instance
from .machine import Machine
from .part import Part


class Source(Machine):
    '''A Device that produces Part objects and supplies them to Devices
    downstream. It is the start of a production line.

    Source will not start producing a next Part until previous Part is
    passed downstream.
    All Parts produced by this Source are copies of the same Part.

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
    starting_parts: int, optional
        Number of available Parts to supply to downstream. Infinite if
        not set.
    '''

    def __init__(self, name = None, sample_part = None, cycle_time = 0.0,
                 starting_parts = float('inf')):
        super().__init__(name, None, cycle_time, value = 0)

        if sample_part == None:
            sample_part = Part()
        else:
            assert_is_instance(sample_part, Part)
        self._sample_part = sample_part

        self._max_produced_parts = starting_parts
        self._cost_of_produced_parts = 0
        self._produced_parts = 0

    def initialize(self, env):
        if self._env == None:
            # First time initialize.
            self._initial_max_produced_parts = self._max_produced_parts
        else:
            # Simulation is resetting, restore starting values.
            self._max_produced_parts = self._initial_max_produced_parts

        super().initialize(env)
        self._sample_part.initialize(env)
        self._cost_of_produced_parts = 0
        self._produced_parts = 0

        self._schedule_finish_processing_part()

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

    @property
    def remaining_parts(self):
        ''' How many Parts parts are left to be produced.
        '''
        return max(self._max_produced_parts - self._produced_parts, 0)

    def _finish_processing_part(self):
        if self._output == None:
            self._output = self._sample_part.make_copy()
            self._output.initialize(self._env)
            self._output.add_routing_history(self)

        self._schedule_pass_part_downstream()

    def _pass_part_downstream(self):
        if self._max_produced_parts - self._produced_parts < 1 or self._output == None:
            return
        supplied_part_value = self._output.value
        super()._pass_part_downstream()
        if self._output == None:  # Part was passed downstream.
            self._produced_parts += 1
            self.add_cost('supplied_part', supplied_part_value)
            self._cost_of_produced_parts += supplied_part_value
            self._env.add_datapoint('supplied_new_part', self.name, (self._env.now,))
            self._schedule_finish_processing_part()

    def adjust_part_count(self, value):
        ''' Update the number of remaining Parts.

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
        # Maximum parts to produce can't be lower than produced parts.
        self._max_produced_parts = max(self._max_produced_parts + value, self._produced_parts)
        self._schedule_finish_processing_part()

