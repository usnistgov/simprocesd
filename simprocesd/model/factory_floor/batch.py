from .part import Part


class Batch(Part):
    '''A type of Part that can contain multiple other Parts.

    Batch is an abstraction used for moving Parts together. It does not
    represent a physical object, just a grouping.

    Arguments
    ---------
    name: str, default=None
        Name of the Part. If name is None then the Part's name will be
        changed to Part_<id>
    parts: list, default=None
        List of Parts contained in the Batch. None means the Batch
        starts empty.

    Attributes
    ----------
    parts: list
        List of Parts contained in the Batch. Can be modified directly
        to change the contents of the Batch.
    '''

    def __init__(self, name = None, parts = None):
        super().__init__(name, 0, 0)
        if parts == None:
            parts = []
        self.parts = parts

    def initialize(self, env):
        super().initialize(env)
        for p in self.parts:
            p.initialize(env)

    @property
    def value(self):
        '''Sum of values of the Parts.
        '''
        return sum([x.value for x in self.parts])

    def add_value(self, label, value):
        raise NotImplementedError('Batch has no inherent value.')

    def add_routing_history(self, device):
        super().add_routing_history(device)
        for p in self.parts:
            p.add_routing_history(device)

    def remove_from_routing_history(self, index):
        super().remove_from_routing_history(index)
        for p in self.parts:
            p.remove_from_routing_history(index)

