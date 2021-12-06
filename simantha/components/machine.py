
from .machine_asset import MachineAsset


class Machine(MachineAsset):

    def __init__(self, name = None, **kwargs):
        super().__init__(name, **kwargs)

