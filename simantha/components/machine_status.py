from ..utils import assert_is_instance


class MachineStatus:

    def initialize(self, env):
        pass

    def got_new_part(self, part):
        pass

    def started_processing_part(self, part):
        pass

    def finished_processing_part(self, part):
        pass

    def failed(self):
        pass

    def restored(self):
        pass
