from ..factory_floor.asset import Asset


class Cms(Asset):
    '''Base class to represent a Condition Monitoring System.

    Note
    ----
    Cms is experimental at this time and is expected to have significant
    changes that may not be backwards compatible.

    Arguments
    ---------
    maintainer: Maintainer
        Maintainer where to issue work orders.
    name: str, default=None
        Name of the Cms. If name is None then it will be changed to
        Cms_<id>
    value: float, default=0
        Starting value of the Cms.
    '''

    def __init__(self, maintainer, name = None, value = 0):
        super().__init__(name, value)

        self.maintainer = maintainer
        self._sensors = []

    def initialize(self, env):
        super().initialize(env)
        self.maintainer.initialize(env)

    def add_sensor(self, sensor):
        '''Register a sensor for the CMS.

        Arguments
        ---------
        sensor: Sensor
            Sensor to be registered.
        '''
        if sensor in self._sensors:
            return

        self._sensors.append(sensor)
        callback = lambda s, time, data: self.on_sense(s, time, data)
        sensor.add_on_sense_callback(callback)

    def on_sense(self, sensor, time, data):
        '''Called every time a registered sensor takes a measurement.

        Arguments
        ---------
        sensor: Sensor
            Sensor that took the measurement.
        time: float
            Simulation time of when the measurement was taken.
        data: list
            Measurement data.
        '''
        pass
