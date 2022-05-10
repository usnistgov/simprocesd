from ...utils import assert_is_instance
from ..system import Environment, System


class Asset:
    '''Base class for all assets in the system. All simulated objects
    should extend this class.

    Arguments:
    name -- name of the asset.
    value -- starting value of the asset.
    is_transitory -- If True the Asset need to be
        initialized/re-initialized manually. For example Part objects
        are initialized by the Source that produced them. If False the
        Asset automatically registers with the System using
        System.add_asset
    '''

    _id_counter = 0

    def __init__(self, name = None, value = 0, is_transitory = False):
        Asset._id_counter += 1
        self._id = Asset._id_counter
        if name == None:
            self._name = f'{type(self).__name__}_{self._id}'
        else:
            self._name = name
        self._env = None
        self._value = self._initial_value = value
        self.value_history = []

        if is_transitory == False:
            System.add_asset(self)

    def initialize(self, env):
        assert_is_instance(env, Environment)
        # Check to avoid using same Assets in multiple Systems, that use
        # case is not supported.
        assert self._env == None or self._env == env, \
            f'Asset {self.name} cannot be initialized by multiple Environments.'
        self._env = env
        self._value = self._initial_value
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

    @property
    def env(self):
        return self._env

    def add_value(self, label, value):
        ''' Add to the value of the asset and record the change in
        value_history - (label, time, value).

        Arguments:
        label -- label to explain change in value.
        value -- how much to increase the value by.
        '''
        self.value_history.append((label, self._env.now, value))
        self._value += value

    def add_cost(self, label, cost):
        ''' Decrease the value of the asset and record the change in
        value_history - (label, time, value).

        Arguments:
        label -- label to explain change in value.
        value -- how much to decrease the value by.
        '''
        self.add_value(label, -cost)

