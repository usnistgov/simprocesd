from ...utils.utils import assert_is_instance
from .asset import Asset
from .part_flow_controller import PartFlowController


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
    quality: float, default=1
        Starting quality of the Part.

    Attributes
    ----------
    quality: float
        A numerical representation for the quality of the Part.
    '''

    def __init__(self, name = None, value = 0, quality = 1):
        super().__init__(name, value, is_transitory = True)

        self.quality = quality
        self._routing_history = []
        self._group_pathing = []

    @property
    def routing_history(self):
        '''Ordered list of devices that the part passed through.
        First entry is usually a Source.
        '''
        return self._routing_history.copy()

    def add_routing_history(self, device):
        '''Adds a device to the end of the routing history.

        Arguments
        ---------
        device: PartFlowController
            Item to be added to routing history.
        '''
        assert_is_instance(device, PartFlowController)
        self._routing_history.append(device)

    def remove_from_routing_history(self, index):
        '''Removes an item from the routing history.

        Arguments
        ---------
        index: int
            Index of an element in the routing history to be removed.

        Raises
        ------
        IndexError
            If the provided index is outside the routing history's
            range.
        '''
        del self._routing_history[index]


class PartGenerator():
    '''Creates new Parts with specified starting parameters.

    Arguments
    ---------
    name_prefix: str
        What the name of each generated Part will start with.
        Generated names follow the pattern: <name_prefix>_<n> where
        <n> starts with 1 and increments with each generated Part.
    value: float, default=0
        Starting value of generated Parts.
    quality: float, default=1
        Starting quality of generated Parts.
    '''

    def __init__(self, name_prefix, value = 0, quality = 1):
        self.name_prefix = name_prefix
        self.value = value
        self.quality = quality

        self._generated_part_counter = 0

    def generate_part(self):
        '''Create a new Part.

        Returns
        -------
        Part
            New uninitialized Part.
        '''
        self._generated_part_counter += 1
        return self.generate_part_helper(f'{self.name_prefix}_{self._generated_part_counter}',
                                          self._generated_part_counter)

    def generate_part_helper(self, part_name, part_counter):
        '''Helper method for generating a new Part.

        Provides additional arguments to make part generation easier.

        Arguments
        ---------
        part_name: str
            Auto-generated name for the new Part. (See class
            description)
        part_counter: int
            Count of the Part being created starting with 1.

        Returns
        -------
        Part
            New uninitialized Part.
        '''
        return Part(name = part_name, value = self.value, quality = self.quality)
