from ..utils import assert_is_instance


class MachineStatus:

    def initialize(self, env):
        pass

    def started_processing_part(self, part):
        pass

    def finished_processing_part(self, part):
        pass
