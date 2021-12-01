
from .machine_asset import MachineAsset
from .machine_status import MachineStatus


class Machine(MachineAsset):

    def __init__(
        self,
        name,
        machine_status = MachineStatus(),
        upstream = [],
        cycle_time = 1.0,
        value = 0.0
    ):
        super().__init__(name, upstream, cycle_time, machine_status, value)

    def initialize(self, env):
        super().initialize(env)

