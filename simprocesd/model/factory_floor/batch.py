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
        is_first_call = self._env == None
        super().initialize(env)

        if is_first_call:
            # The first time initialize is called.
            self._initial_parts = [p.make_copy() for p in self.parts]
        else:
            # Simulation is resetting.
            self.parts = [p.make_copy() for p in self._initial_parts]

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

    def make_copy(self):
        self.copy_counter += 1
        new_batch = Batch(f'{self.name}_{self.copy_counter}')
        for p in self.parts:
            new_batch.parts.append(p.make_copy())
        return new_batch
