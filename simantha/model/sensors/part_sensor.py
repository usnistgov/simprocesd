from ...utils import assert_is_instance
from ..factory_floor.machine import Machine
from .sensor import Sensor


class OutputPartSensor(Sensor):
    ''' Probes processed parts of a Machine.

    Arguments:
    machine -- machine whose parts to probe
    probing_interval -- how many parts to skip after last probed part.

    '''

    def __init__(self,
                 machine,
                 part_probes,
                 probing_interval = 0,
                 ** kwargs):
        assert_is_instance(machine, Machine)
        super().__init__(machine, part_probes, **kwargs)

        self._machine = machine
        self._probing_interval = probing_interval
        self._counter = self._probing_interval

    def initialize(self, env):
        super().initialize(env)
        self._machine.add_finish_processing_callback(self._probe_part)

    def _probe_part(self, part):
        self._counter -= 1
        if self._counter < 0:
            for p in self._probes:
                p.target = part
            self.sense()
            self._counter = self._probing_interval

