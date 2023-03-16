from ...utils.utils import assert_is_instance
from .asset import Asset
from .device import Device


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
        '''Ordered list of devices that the part passed through.
        First entry is usually a Source.
        '''
        return self._routing_history.copy()

    def add_routing_history(self, device):
        assert_is_instance(device, Device)
        self._routing_history.append(device)

    def make_copy(self):
        ''' Create a copy of this Part.

        Returns
        -------
        Part
            a copy of this Part with a unique ID and an empty
            routing_history. Returned Part is not initialized.
        '''
        self.copy_counter += 1
        new_part = Part(f'{self.name}_{self.copy_counter}', self.value, self.quality)
        return new_part
