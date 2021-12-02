from .asset import Asset


class Part(Asset):

    def __init__(self, name = None, value = 0.0, quality = 1.0):
        super().__init__(name, value)

        self._counter = 0
        self.quality = quality

        self.routing_history = []

    def copy(self):
        self._counter += 1
        new_part = Part(f'{self.name}_{self._counter}', self.value, self.quality)
        return new_part
