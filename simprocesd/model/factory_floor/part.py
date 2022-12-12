from .asset import Asset


class Part(Asset):
    '''Representation of an item/part that passes between Devices in a
    production line.

    Arguments
    ---------
    name: str, default=None
        Name of the Part. If name is None then the Part's name will be
        changed to Part_<id>
    value: float, default=0
        Starting value of the Part.
    quality: float, default=1.0
        Starting quality of the Part.

    Attributes
    ----------
    quality: float
        A numerical representation for the quality of the Part.
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
        ''' Ordered list of devices that the part passed
        through. First entry is usually a Source.

        Warning
        -------
        Predefined classes (Source, Device, etc) contain code for
        updating the routing history so a custom subclass is responsible
        for ensuring those updates still happen or it might not appear
        in the routing history.
        '''
        return self._routing_history

    def make_copy(self):
        ''' Create a copy of this Part.

        Returns
        -------
        Part
            a copy of this Part with a unique ID and an empty
            routing_history.
        '''
        self.copy_counter += 1
        new_part = Part(f'{self.name}_{self.copy_counter}', self.value, self.quality)
        return new_part
