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
        if sensor in self._sensors:
            return

        self._sensors.append(sensor)
        callback = lambda s, time, data: self.on_sense(s, time, data)
        sensor.add_on_sense_callback(callback)

    def on_sense(self, sensor, time, data):
        pass
