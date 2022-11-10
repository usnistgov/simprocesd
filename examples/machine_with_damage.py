from simprocesd.model.factory_floor import Machine
from simprocesd.model.simulation import EventType
from simprocesd.utils import geometric_distribution_sample, assert_callable


class MachineWithDamage(Machine):
    ''' A Machine that periodically accumulates damage and that can be
    maintained to reset accumulated damage.

    Arguments:
    name -- name of the machine.
    upstream -- list of upstream devices.
    cycle_time -- how long it takes to complete one process cycle.
    value -- starting value of the machine.
    period_to_degrade -- how often the machine will degrade. Values
        equal or less than zero mean never (default).
    probability_to_degrade -- chance of the machine to accumulate
        damage every degrade period.
    damage_on_degrade -- how much damage to accumulate at a time.
    damage_to_fail -- accumulated damage threshold when the machine
        fails.
    get_maintenance_duration -- a function that returns the duration
        of the maintenance.
        Callback signature: callback(machine, maintenance_tag)
    get_capacity_to_maintain -- a function that returns the needed
        maintainer capacity for machine maintenance.
        Callback signature: callback(machine, maintenance_tag)
    get_cost_to_maintain -- a function that returns the Maintainer
        cost in order to maintain this machine.
        Callback signature: callback(machine, maintenance_tag)
    '''

    def __init__(self,
                 name = None,
                 upstream = [],
                 cycle_time = 0,
                 value = 0,
                 period_to_degrade = -1,
                 probability_to_degrade = 0,
                 damage_on_degrade = 1,
                 damage_to_fail = float('inf'),
                 get_maintenance_duration = lambda machine, tag: 0,
                 get_capacity_to_maintain = lambda machine, tag: 0,
                 get_cost_to_maintain = lambda machine, tag: 0):
        super().__init__(name, upstream, cycle_time, value)
        self._damage = 0
        self._period_to_degrade = period_to_degrade
        self._damage_on_degrade = damage_on_degrade
        self._damage_to_fail = damage_to_fail
        self._probability_to_degrade = probability_to_degrade
        self._get_maintenance_duration = get_maintenance_duration
        self._get_capacity_to_maintain = get_capacity_to_maintain
        self._get_cost_to_maintain = get_cost_to_maintain
        self._on_degrade_callbacks = []

    @property
    def damage(self):
        ''' Represents accrued wear and tear on the machine.
        '''
        return self._damage

    @damage.setter
    def damage(self, value):
        self._env.add_datapoint('damage_update', self.name, (self._env.now, value))
        self._damage = value

    def initialize(self, env):
        super().initialize(env)
        self.damage = 0
        self._prepare_next_degrade_event()

    def add_on_degrade_callback(self, callback):
        ''' Adds a callback to be called when status degrades.

        Arguments:
        callback -- function with a signature callback(this_machine)
        '''
        assert_callable(callback)
        self._on_degrade_callbacks.append(callback)

    def _is_operational(self):
        return self.damage < self._damage_to_fail

    def _prepare_next_degrade_event(self):
        if self._period_to_degrade <= 0 or self._probability_to_degrade <= 0:
            return

        time_to_degrade = geometric_distribution_sample(
                self._probability_to_degrade, 1) * self._period_to_degrade
        self._env.schedule_event(self._env.now + time_to_degrade,
                                 self.id,
                                 self._degrade,
                                 EventType.OTHER_HIGH_PRIORITY,
                                 f'Machine degrade.')

    def _degrade(self):
        self.damage += self._damage_on_degrade
        if self._is_operational():
            self._prepare_next_degrade_event()
        else:
            self.schedule_failure(self._env.now,
                    f'{self.name} degraded to failure.')
        for c in self._on_degrade_callbacks:
            c(self)

    # Beginning of Maintainable function overrides.
    def get_work_order_duration(self, tag):
        return self._get_maintenance_duration(self, tag)

    def get_work_order_capacity(self, tag):
        return self._get_capacity_to_maintain(self, tag)

    def get_work_order_cost(self, tag):
        return self._get_cost_to_maintain(self, tag)

    def start_work(self, tag):
        self.shutdown()

    def end_work(self, tag):
        was_operational = self._is_operational()
        self.damage = 0

        # Next degrade event was not scheduled if machine was not
        # operational.
        if not was_operational:
            self._prepare_next_degrade_event()
        self.restore_functionality()
    # End of Maintainable function overrides.

