from ..utils import assert_is_instance


class MachineStatus:

    def __init__(self, get_time_to_fix = lambda: 1):
        self._get_time_to_fix = get_time_to_fix

    @property
    def time_to_fix(self):
        return self._get_time_to_fix()

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

    def __init__(self, get_time_to_failure, **kwargs):
        super().__init__(**kwargs)
        assert callable(get_time_to_failure), 'get_time_to_failure needs to be a callable.'
        self._get_ttf = get_time_to_failure

    def initialize(self, machine, env):
        self._machine = machine
        self._env = env
        self.schedule_failure()

    def restored(self):
        self.schedule_failure()

    def schedule_failure(self):
        self._machine.schedule_failure(self._env.now + self._get_ttf())
