from ...utils import assert_is_instance
from ..factory_floor.machine import Machine
from .sensor import Sensor


class OutputPartSensor(Sensor):
    '''Sensor for measuring a Machine's processed Parts.

    Will measure Parts that the Machine finished processing, Part does
    have to pass downstream before it is measured.

    Arguments
    ---------
    machine: Machine
        A Machine whose produced parts will be measured.
    sensing_interval: int, default=0
        How many Parts to skip after last measured Part.
        Setting this to 0 means every part will be checked. First Part
        is always measured.
    name: str, default=None
        Name of the object. If name is None then the object's name will
        be changed to OutputPartSensor_<id>
    data_capacity: int, optional
        Number of most recent entries to store. Limits the object's
        maximum memory usage.
    value: float, default=0
        Starting value of the OutputPartSensor.
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

    def _probe_part(self, machine, part):
        self._counter -= 1
        if self._counter < 0:
            for p in self._probes:
                p.target = part
            self.sense()
            self._counter = self._probing_interval

