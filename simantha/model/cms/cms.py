from ..factory_floor.asset import Asset


class Cms(Asset):
    ''' Based class to represent a Condition Monitoring System.
    '''

    def __init__(self, maintainer, name = None, value = 0):
        super().__init__(name, value)

        self.maintainer = maintainer
        self._sensors = []

    def initialize(self, env):
        super().initialize(env)
        self.maintainer.initialize(env)
        for s in self._sensors:
            s.initialize(env)

    def add_sensor(self, sensor):
        self._sensors.append(sensor)
        # user_data can be manipulated directly from sensor
        callback = lambda sensor_target, data:self.on_sense(sensor, data)
        sensor.add_on_sense_callback(callback)

    def on_sense(self, sensor, data):
        pass
