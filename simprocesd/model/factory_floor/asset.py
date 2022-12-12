from ...utils import assert_is_instance
from ..system import Environment, System


class Asset:
    '''Base class to be used for all simulated assets in production.

    Arguments
    ----------
    name: str, default=None
        Name of the Asset. If name is None then the Asset's name will be
        changed to Asset_<id>
    value: float, default=0
        Starting value of the Asset.
    is_transitory: bool, default=False
        If True the Asset needs to be initialized/re-initialized
        manually. For example, Part objects are initialized by the
        Source that produced them.
        If False then the Asset automatically registers with the System
        which will handle object initialization.
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
        '''Prepare asset for simulation and reset attributes to
        starting values.

        In most cases this is called automatically by the System. Needs
        to be called manually if the Asset was initialized with
        is_transitory set to True.

        Arguments
        ----------
        env: Environment
            Environment used by the simulating System.
        '''
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
        '''Name of the Asset.
        '''
        return self._name

    @property
    def id(self):
        '''Unique Asset ID.
        '''
        return self._id

    @property
    def value(self):
        '''Current value of the Asset.
        '''
        return self._value

    @property
    def env(self):
        '''Simulation's Environment instance or None if the Asset has
        not been initialized yet
        '''
        return self._env

    @property
    def value_history(self):
        '''History of value changes for this Asset. Each entry contains:
            (label, time of change, value delta, new asset value)
        '''
        return self._value_history

    def add_value(self, label, value):
        '''Add to the value of the Asset and record the change in
        value_history.

        Arguments
        ----------
        label: str
            Label for the change in value.
        value: float
            By how much to increase the Asset's value. Value of 0 is
            ignored.
        '''
        if value == 0:
            return
        self._value += value
        self._value_history.append((label, self._env.now, value, self._value))

    def add_cost(self, label, cost):
        ''' Decrease the value of the Asset and record the change in
        value_history.

        Arguments
        ----------
        label: str
            Label for the change in value
        cost: float
            By how much to decrease the Asset's value. Value of 0 is
            ignored.
        '''
        self.add_value(label, -cost)

