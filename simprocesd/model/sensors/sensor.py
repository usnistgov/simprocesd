from ...utils import assert_is_instance, assert_callable
from ..factory_floor import Asset
from ..simulation import EventType


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
        super().__init__(lambda t: getattr(t, self._attribute_name, None), target)


class Sensor(Asset):
    ''' Sensor uses provided probes to collect data and store it under
    the data attribute. data attribute is a dictionary of lists filled
    with probe data and the dictionary is indexed by probe.

    Arguments:
    probes -- list of probes to use.
    name -- name of the sensor.
    data_capacity -- number of most recent entries to store. Helps limit
        sensor's memory usage for very long simulation.
    value -- value of the sensor.

    '''

    def __init__(self,
                 probes,
                 name = None,
                 data_capacity = float('inf'),
                 value = 0):
        super().__init__(name, value)

        assert data_capacity >= 1, 'Data capacity cannot be less than 1.'
        self._data_capacity = data_capacity
        self._on_sense = []
        self._last_sense = []

        assert_is_instance(probes, list)
        assert len(probes) > 0, 'No probes were specified.'
        self._probes = probes

        self.data = {}
        for p in self._probes:
            self.data[p] = []

    def initialize(self, env):
        super().initialize(env)

        self._last_sense = []

        self.data = {}
        for p in self._probes:
            self.data[p] = []

    def add_on_sense_callback(self, callback):
        ''' callback(sensor/self, time, sense_data)

        Arguments:
        time -- current simulation time.
        sense_data -- list of probe data [probe1_data, probe2_data,...]
        '''
        assert_callable(callback)
        self._on_sense.append(callback)

    def _collect_data(self):
        self._last_sense = []
        for p in self._probes:
            new_data = p.probe()
            self.data[p].append(new_data)
            self._last_sense.append(new_data)

        if len(self.data[self._probes[0]]) > self._data_capacity:
            for p in self._probes:
                self.data[p].pop(0)  # drop oldest data

    def sense(self):
        self._collect_data()
        for c in self._on_sense:
            c(self, self._env.now, self.last_sense)

    @property
    def last_sense(self):
        return self._last_sense

    @property
    def probes(self):
        return self._probes.copy()


class PeriodicSensor(Sensor):

    def __init__(self,
                 interval,
                 probes,
                 name = None,
                 data_capacity = 10000,
                 value = 0
                 ):
        super().__init__(probes, name, data_capacity, value)

        self._interval = interval

    def initialize(self, env):
        super().initialize(env)
        self.data['time'] = []
        self._periodic_sense()

    def _periodic_sense(self):
        self.data['time'].append(self._env.now)
        self.sense()
        self.schedule_next_sense()

    def schedule_next_sense(self):
        self._env.schedule_event(
            self._env.now + self._interval,
            self.id,
            self._periodic_sense,
            EventType.SENSOR,
            f'Periodic sense by {self.name}'
        )
