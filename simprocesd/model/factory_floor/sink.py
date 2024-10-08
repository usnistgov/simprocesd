from . import Batch, PartHandler


class Sink(PartHandler):
    '''A Device that can receive any number of Parts but not pass
    those Parts. It is the end of a production line.

    Note
    ----
    Sink's value will increase by the value attribute of each received
    Part. This is how Sink tracks the output value of produced Parts.

    Arguments
    ----------
    name: str, default=None
        Name of the Sink. If name is None then the Sink's name will
        be changed to Sink_<id>
    upstream: list of PartFlowController, default=None
        List of devices from which Parts can be received.
    cycle_time: float, default=0
        Minimum time between receiving Parts.
    collect_parts: bool, default=False
        If True then received Parts are stored throughout the simulation
        and can be accessed under 'collected_parts'.

    Attributes
    ----------
    collected_parts: list
        List of received Parts in the order they were received.
    '''

    def __init__(self,
                 name = None,
                 upstream = None,
                 cycle_time = 0,
                 collect_parts = False):
        super().__init__(name, upstream, cycle_time = cycle_time, value = 0)

        self._collect_parts = collect_parts
        self.collected_parts = []
        self._received_parts_count = 0
        self._value_of_received_parts = 0

    def _add_downstream(self, downstream):
        raise RuntimeError('Sink cannot have any downstreams.')

    @property
    def received_parts_count(self):
        '''Count of all received Parts.

        When receiving a Batch this will increase by the number of Parts
        contained within the Batch.
        '''
        return self._received_parts_count

    @property
    def value_of_received_parts(self):
        '''Summed value of all received Parts.
        '''
        return self._value_of_received_parts

    def _on_received_new_part(self):
        if isinstance(self._part, Batch):
            self._received_parts_count += len(self._part.parts)
        else:
            self._received_parts_count += 1
        self._value_of_received_parts += self._part.value
        self.add_value(f'collected_part', self._part.value)
        if self._collect_parts:
            self.collected_parts.append(self._part)

        super()._on_received_new_part()

    def _finish_cycle(self):
        super()._finish_cycle()
        self._output = None
        self.notify_upstream_of_available_space()

    def _schedule_pass_part_downstream(self):
        pass  # Sink does not pass parts anywhere.

