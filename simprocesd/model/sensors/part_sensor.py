from ...utils import assert_is_instance
from ..factory_floor.machine import Machine
from .sensor import Sensor


class OutputPartSensor(Sensor):
    ''' Probes processed parts of a Machine.

    Arguments:
    machine -- machine whose produced parts will be probed.
    sensing_interval -- how many parts to skip after last probed part.
        Setting this to 0 means every part will be checked. First part
        is always probed by the sensor.
    name -- name of the sensor.
    data_capacity -- number of most recent entries to store. Useful for
        very long simulation where memory may become an issue.
    value -- value of the sensor.
    '''

    def __init__(self,
                 machine,
                 part_probes,
                 sensing_interval = 0,
                 name = None,
                 data_capacity = float('inf'),
                 value = 0):
        assert_is_instance(machine, Machine)
        super().__init__(part_probes, name, data_capacity, value)

        self._machine = machine
        assert sensing_interval >= 0, 'Probing interval cannot be less than 0.'
        self._probing_interval = sensing_interval
        self._counter = 0

    def initialize(self, env):
        if self._env == None:
            self._machine.add_finish_processing_callback(self._probe_part)

        super().initialize(env)
        self._counter = 0

    def _probe_part(self, part):
        self._counter -= 1
        if self._counter < 0:
            for p in self._probes:
                p.target = part
            self.sense()
            self._counter = self._probing_interval

