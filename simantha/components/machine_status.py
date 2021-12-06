from ..utils import assert_is_instance


class MachineStatus:

    def initialize(self, machine, env):
        self._machine = machine
        self._env = env

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


class PeriodicFailStatus(MachineStatus):

    def __init__(self, get_time_to_failure):
        assert callable(get_time_to_failure), 'get_time_to_failure needs to be a callable.'
        self._get_ttf = get_time_to_failure

    def initialize(self, machine, env):
        self._machine = machine
        self._env = env
        self._machine.schedule_machine_failure(self._get_ttf())

    def restored(self):
        self._machine.schedule_machine_failure(self._get_ttf())
