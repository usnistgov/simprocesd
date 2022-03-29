from ..factory_floor import Asset
from ..simulation import EventType
from ...utils import assert_is_instance, assert_callable


class Probe:

    def __init__(self, get_data, target):
        assert_callable(get_data, False)
        self._get_data = get_data
        self.target = target

    def probe(self):
        return self._get_data(self.target)


class AttributeProbe(Probe):

    def __init__(self, attribute_name, target):
        assert_is_instance(attribute_name, str)
        self._attribute_name = attribute_name
        super().__init__(lambda t: getattr(t, self._attribute_name, None),
                         target)


class Sensor(Asset):

    def __init__(self,
                 target,
                 probes,
                 name = None,
                 data_capacity = 10000,
                 value = 0):
        super().__init__(name, value)

        assert target != None, 'Target cannot be None.'
        self._target = target
        self.data = {}
        self._data_capacity = data_capacity
        self._on_sense = []

        assert_is_instance(probes, list)
        assert len(probes) > 0, 'No probes were specified.'
        self._probes = probes

        for p in self._probes:
            self.data[p] = []

    def add_on_sense_callback(self, callback):
        ''' callback(target_machine, sense_data)
        sense_data -- list of probe data [probe1_data, probe2_data,...]
        '''
        assert_callable(callback)
        self._on_sense.append(callback)

    def _collect_data(self):
        for p in self._probes:
            self.data[p].append(p.probe())

        if len(self.data[self._probes[0]]) > self._data_capacity:
            for p in self._probes:
                self.data[p].pop(0)  # drop oldest data

    def sense(self):
        self._collect_data()
        for c in self._on_sense:
            c(self._target, self.last_sense)

    @property
    def last_sense(self):
        rtn = []
        for p in self._probes:
            rtn.append(self.data[p][-1])
        return rtn


class PeriodicSensor(Sensor):

    def __init__(self,
                 target,
                 interval,
                 probes,
                 name = None,
                 data_capacity = 10000,
                 value = 0
                 ):
        super().__init__(target, probes, name, data_capacity, value)

        self._interval = interval

    def initialize(self, env):
        super().initialize(env)
        self.schedule_next_sense()

    def _periodic_sense(self):
        self.sense()
        self.schedule_next_sense()

    def schedule_next_sense(self):
        self._env.schedule_event(
            self._env.now + self._interval,
            self.id,
            self._periodic_sense,
            EventType.SENSOR,
            f'{self._target.name}'
        )
