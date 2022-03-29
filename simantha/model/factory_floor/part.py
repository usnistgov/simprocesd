from .asset import Asset


class Part(Asset):
    ''' Basic part with attributes to be passed between machines in the
    simulation.
    '''

    def __init__(self, name = None, value = 0.0, quality = 1.0):
        super().__init__(name, value)

        self._counter = 0
        self.quality = quality

        self.routing_history = []

    def copy(self):
        ''' Creates and returns a new and unique Part with same
        attributes as this part.
        New Part will not have the same id and routing_history will
        start empty.
        '''
        self._counter += 1
        new_part = Part(f'{self.name}_{self._counter}', self.value, self.quality)
        return new_part
