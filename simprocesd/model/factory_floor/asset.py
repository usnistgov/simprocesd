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
        are initialized by the Source that produced them. If False
        then the Asset automatically registers with the System using
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
        self._value_history = []

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
        self._value_history = []

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

    @property
    def value_history(self):
        ''' A list of tuples tracking Asset's value changes.
        Tuple composition: (label, time, value_change, new_value)
          label - label provided with the change in value.
          time - simulation time when the value was changed.
          value_change - by how much the value was changed.
          new_value - Asset's value after the value change.
        '''
        return self._value_history

    def add_value(self, label, value):
        ''' Add to the value of the Asset and record the change in
        value_history.

        Arguments:
        label -- label for the change in value.
        value -- how much to increase the Asset's value by.
        '''
        self._value += value
        self._value_history.append((label, self._env.now, value, self._value))

    def add_cost(self, label, cost):
        ''' Decrease the value of the Asset and record the change in
        value_history.

        Arguments:
        label -- label for the change in value.
        cost -- how much to decrease the Asset's value by.
        '''
        self.add_value(label, -cost)

