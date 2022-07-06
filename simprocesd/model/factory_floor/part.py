from .asset import Asset


class Part(Asset):
    ''' Basic part with attributes to be passed between devices in the
    simulation.

    Arguments:
    name -- name of the part.
    value -- starting value of the part.
    quality -- starting quality of the part.
    '''

    def __init__(self, name = None, value = 0.0, quality = 1.0):
        super().__init__(name, value, is_transitory = True)

        self.copy_counter = 0
        self.quality = self._initial_quality = quality
        self._routing_history = []

    def initialize(self, env):
        super().initialize(env)
        self.quality = self._initial_quality
        self._routing_history = []
        self.copy_counter = 0

    @property
    def routing_history(self):
        ''' Contains an ordered list of devices that the part passed
        through. First entry is usually a Source.
        NOTE: Devices may not be configured to add themselves to the
        routing_history and would then not appear in any part's
        routing_history.
        '''
        return self._routing_history

    def make_copy(self):
        ''' Creates and returns a new and unique Part with same
        attributes as this part.
        New Part will not have the same id and new Part's
        routing_history will start empty.
        '''
        self.copy_counter += 1
        new_part = Part(f'{self.name}_{self.copy_counter}', self.value, self.quality)
        return new_part
