import copy

from ...utils import assert_is_instance, assert_callable
from ..factory_floor import Asset
from ..simulation import EventType


class Probe:
    '''Measuring component of a Sensor.

    Arguments
    ---------
    get_data: function
        A function that represents taking a measurement. Function
        signature is get_data(target) and it must return the measurement
        data.
    target: object
        Target of the probe.
    '''

    def __init__(self, get_data, target):
        assert_callable(get_data, False)
        self._get_data = get_data
        self.target = target

    def probe(self):
        '''Take a measurement with this Probe.

        Returns
        -------
        object
            Measurement data.
        '''
        return copy.copy(self._get_data(self.target))


class AttributeProbe(Probe):
    '''A probe that measures an object's attribute.

    Arguments
    ---------
    attribute_name: str
        Name of the attribute to be measured.
    target: object
        Target of the probe.
    '''

    def __init__(self, attribute_name, target):
        assert_is_instance(attribute_name, str)
        self._attribute_name = attribute_name
        super().__init__(lambda t: getattr(t, self._attribute_name, None), target)


class Sensor(Asset):
    '''A Sensor uses Probes to collect data and store that data.

    When a measurement is taken the Sensor will use all provided Probes
    and record that data.

    Arguments
    ---------
    probes: list
        List of probes to use for measurements.
    name: str, optional
        Name of the Sensor. If name is None then the Sensor's name will
        be changed to Sensor_<id>
    data_capacity: int, optional
        Number of most recent entries to store. Limits the Sensor's
        maximum memory usage.
    value: float, default=0
        Starting value of the Sensor.

    Attributes
    ----------
    data: dictionary
        Key: probe object. Value: list of probe data in the order the
        measurements were taken.
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
        '''Register a function to be called every time sensor makes a
        measurement.

        | The callback function will be called with:
        | time: float
        |     Current simulation time.
        | sense_data: list
        |     List of probe data [probe1_data, probe2_data, ...]

        Arguments
        ---------
        callback: function
            callback(sensor, time, sense_data)
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
        '''Make Sensor take a measurement with all of its probes and
        record the data.
        '''
        self._collect_data()
        for c in self._on_sense:
            c(self, self._env.now, self.last_sense)

    @property
    def last_sense(self):
        '''List of Probe measurement data from the last measurement or
        an empty list if no measurement has been made yet.
        '''
        return self._last_sense

    @property
    def probes(self):
        '''List of Sensor's Probes.
        '''
        return self._probes.copy()


class PeriodicSensor(Sensor):
    '''Sensor that takes a periodic measurement.

    First measurement is made at simulation time <interval>

    Arguments
    ---------
    interval: float
        Duration of time between measurements. Measured in simulation
        time.
    probes: list
        List of probes to use for measurements.
    name: str, optional
        Name of the Sensor. If name is None then the Sensor's name will
        be changed to Sensor_<id>
    data_capacity: int, optional
        Number of most recent entries to store. Limits the Sensor's
        maximum memory usage.
    value: float, default=0
        Starting value of the Sensor.
    '''

    def __init__(self,
                 interval,
                 probes,
                 name = None,
                 data_capacity = float('inf'),
                 value = 0):
        super().__init__(probes, name, data_capacity, value)

        self._interval = interval

    def initialize(self, env):
        super().initialize(env)
        self.data['time'] = []
        self._schedule_next_sense()

    def _periodic_sense(self):
        self.data['time'].append(self._env.now)
        self.sense()
        self._schedule_next_sense()

    def _schedule_next_sense(self):
        self._env.schedule_event(
            self._env.now + self._interval,
            self.id,
            self._periodic_sense,
            EventType.SENSOR,
            f'Periodic sense by {self.name}'
        )
