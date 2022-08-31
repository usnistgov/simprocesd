from simprocesd.model.factory_floor import MachineStatusTracker
from simprocesd.model.simulation import EventType
from simprocesd.utils import geometric_distribution_sample, assert_callable


class StatusTrackerWithDamage(MachineStatusTracker):

    def __init__(self,
                 period_to_degrade,
                 probability_to_degrade,
                 damage_on_degrade,
                 damage_to_fail = float('inf'),
                 get_time_to_maintain = lambda damage: 0,
                 get_capacity_to_maintain = lambda damage: 0,
                 get_cost_to_maintain = lambda damage: 0):
        super().__init__()
        self._damage = 0
        self._period_to_degrade = period_to_degrade
        self._damage_on_degrade = damage_on_degrade
        self._damage_to_fail = damage_to_fail
        self._probability_to_degrade = probability_to_degrade
        self._get_time_to_maintain = get_time_to_maintain
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
        self._env.add_datapoint('damage_update', self._machine.name, (self._env.now, value))
        self._damage = value

    def initialize(self, machine, env):
        super().initialize(machine, env)
        self.damage = 0  # records initial datapoint
        self._prepare_next_degrade_event()

    def _prepare_next_degrade_event(self):
        if self._probability_to_degrade <= 0: return

        time_to_degrade = geometric_distribution_sample(
                self._probability_to_degrade, 1) * self._period_to_degrade
        self._env.schedule_event(self._env.now + time_to_degrade,
                                 self._machine.id,
                                 self._degrade,
                                 EventType.OTHER_HIGH_PRIORITY,
                                 f'Machine degrade event.')

    def _degrade(self):
        self.damage += self._damage_on_degrade
        if self.is_operational():
            self._prepare_next_degrade_event()
        else:
            self._machine.schedule_failure(self._env.now,
                    f'{self._machine.name} failed from wear and tear degradation.')
        for c in self._on_degrade_callbacks:
            c(self.damage)

    def maintain(self, maintenance_tag):
        was_operational = self.is_operational()

        self._machine.add_cost(f'maintenance', self._get_cost_to_maintain(self.damage))
        self.damage = 0

        if not was_operational:
            self._prepare_next_degrade_event()

    def get_time_to_maintain(self, maintenance_id):
        return self._get_time_to_maintain(self.damage)

    def get_capacity_to_maintain(self, maintenance_id):
        return self._get_capacity_to_maintain(self.damage)

    def is_operational(self):
        return self.damage < self._damage_to_fail

    def add_on_degrade_callback(self, callback):
        ''' Adds a callback to be called when status degrades.

        Arguments:
        callback -- function with a signature callback(damage)
        '''
        assert_callable(callback)
        self._on_degrade_callbacks.append(callback)

