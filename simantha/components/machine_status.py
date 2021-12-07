from ..utils import assert_is_instance


class MachineStatus:

    def __init__(self, get_time_to_fix = lambda: 1):
        self._get_time_to_fix = get_time_to_fix

        self.receive_part_callback = lambda x: None
        self.start_processing_callback = lambda x: None
        self.finish_processing_callback = lambda x: None
        self.failed_callback = lambda: None
        self.restored_callback = lambda: None
        self._machine = None
        self._env = None

    @property
    def machine(self):
        return self._machine

    @property
    def time_to_fix(self):
        return self._get_time_to_fix()

    def initialize(self, machine, env):
        self._machine = machine
        self._env = env

    def set_receive_part_callback(self, callback):
        assert callable(callback), 'callback needs to be callable.'
        self.receive_part_callback = callback

    def set_start_processing_callback(self, callback):
        assert callable(callback), 'callback needs to be callable.'
        self.start_processing_callback = callback

    def set_finish_processing_callback(self, callback):
        assert callable(callback), 'callback needs to be callable.'
        self.finish_processing_callback = callback

    def set_failed_callback(self, callback):
        assert callable(callback), 'callback needs to be callable.'
        self.failed_callback = callback

    def set_restored_callback(self, callback):
        assert callable(callback), 'callback needs to be callable.'
        self.restored_callback = callback


class PeriodicFailStatus(MachineStatus):

    def __init__(self, get_time_to_failure, **kwargs):
        super().__init__(**kwargs)
        assert callable(get_time_to_failure), 'get_time_to_failure needs to be callable.'
        self._get_ttf = get_time_to_failure

    def initialize(self, machine, env):
        self._machine = machine
        self._env = env

        self.set_restored_callback(self.schedule_failure)
        self.schedule_failure()

    def schedule_failure(self):
        self._machine.schedule_failure(self._env.now + self._get_ttf())
