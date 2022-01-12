from ..system import Environment
from ...utils import assert_is_instance


class Asset:
    '''Base class for all assets in the system. All simulated objects should
    extend this class.
    '''

    _id_counter = 0

    def __init__(self, name = None, value = 0):
        Asset._id_counter += 1
        self._id = Asset._id_counter

        if name == None:
            self._name = f'{type(self)}_{self._id}'
        else:
            self._name = name

        self._env = None
        self._value = value
        self.value_history = []

    @property
    def name(self):
        return self._name

    @property
    def id(self):
        return self._id

    @property
    def value(self):
        return self._value

    def initialize(self, env):
        assert self._env == None, f'Initialize called twice on {self.name}'
        assert_is_instance(env, Environment)
        self._env = env

    def add_value(self, label, value):
        self.value_history.append((label, self._env.now, value))
        self._value += value

    def add_cost(self, label, cost):
        self.add_value(label, -cost)

