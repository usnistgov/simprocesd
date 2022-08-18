from .machine import Machine


class Sink(Machine):
    ''' A device that can receive any number of Parts but not pass
    those parts.

    Arguments:
    name -- device name.
    upstream -- list of upstream devices.
    cycle_time -- minimum time between receiving parts.
    collect_parts -- if True then received parts are stored in the
        attribute 'collected_parts' as a list in the order they were
        received.
    '''

    def __init__(self,
                 name = None,
                 upstream = [],
                 cycle_time = 0,
                 collect_parts = False):
        super().__init__(name, upstream, cycle_time = cycle_time, value = 0)

        self._collect_parts = collect_parts
        self.collected_parts = []
        self._received_parts_count = 0
        self._value_of_received_parts = 0

    def initialize(self, env):
        super().initialize(env)
        self.collected_parts = []
        self._received_parts_count = 0
        self._value_of_received_parts = 0

    def _add_downstream(self, downstream):
        raise RuntimeError('Sink cannot have any downstreams.')

    @property
    def received_parts_count(self):
        ''' Returns the count of the received parts.
        '''
        return self._received_parts_count

    @property
    def value_of_received_parts(self):
        ''' Returns the summed value of the received parts.
        '''
        return self._value_of_received_parts

    def _on_received_new_part(self):
        self._received_parts_count += 1
        self._value_of_received_parts += self._part.value
        self.add_value(f'collected_part', self._part.value)
        self._env.add_datapoint('collected_part', self.name,
                                (self._env.now, self._part.quality, self._part.value))
        if self._collect_parts:
            self.collected_parts.append(self._part)

        super()._on_received_new_part()

    def _finish_processing_part(self):
        super()._finish_processing_part()
        self._output = None
        self.notify_upstream_of_available_space()

    def _schedule_pass_part_downstream(self):
        pass  # Sink does not pass parts anywhere.

