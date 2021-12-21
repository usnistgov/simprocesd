from .asset import Asset


class CMS(Asset):

    def __init__(self, maintainer, **kwargs):
        super().__init__(**kwargs)

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
        callback = lambda ud, d:self.on_sense(sensor, d)
        sensor.add_on_sense_callback(callback)

    def on_sense(self, sensor, data):
        pass
