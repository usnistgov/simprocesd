from ..model.factory_floor import MachineStatusTracker
from ..model.simulation import EventType
from ..utils import geometric_distribution_sample


class StatusTrackerWithDamage(MachineStatusTracker):

    def __init__(self,
                 period_to_degrade,
                 probability_to_degrade,
                 damage_on_degrade,
                 damage_to_fail = float('inf'),
                 get_time_to_maintain = lambda damage: 0,
                 get_capacity_to_maintain = lambda damage: 0,
                 get_cost_to_maintain = lambda damage: 0,
                 receive_part_callback = None):
        super().__init__()
        self._damage = 0  # represents wear and tear on the machine
        self._period_to_degrade = period_to_degrade
        self._damage_on_degrade = damage_on_degrade
        self._damage_to_fail = damage_to_fail
        self._probability_to_degrade = probability_to_degrade
        # callback(machine_damage)
        self._get_time_to_maintain = get_time_to_maintain
        # callback(machine_damage)
        self._get_capacity_to_maintain = get_capacity_to_maintain
        # callback(machine_damage)
        self._get_cost_to_maintain = get_cost_to_maintain
        # callback(part, machine_damage)
        self._receive_part_callback = receive_part_callback

    @property
    def damage(self):
        return self._damage

    @damage.setter
    def damage(self, value):
        self._env.add_datapoint('damage_update', self._machine.name, (self._env.now, value))
        self._damage = value

    def initialize(self, machine, env):
        super().initialize(machine, env)
        self.damage = 0  # records initial datapoint
        self._prepare_next_degrade_event()
        if self._receive_part_callback != None:
            self._machine.add_receive_part_callback(
                    lambda p: self._receive_part_callback(p, self.damage))

    def _prepare_next_degrade_event(self):
        if self._probability_to_degrade <= 0: return

        time_to_degrade = geometric_distribution_sample(
                self._probability_to_degrade, 1) * self._period_to_degrade
        self._env.schedule_event(self._env.now + time_to_degrade,
                                 self._machine.id,
                                 self._degrade,
                                 EventType.OTHER_HIGH,
                                 f'Machine degrade event.')

    def _degrade(self):
        self.damage += self._damage_on_degrade
        if self.is_operational():
            self._prepare_next_degrade_event()
        else:
            self._machine.schedule_failure(self._env.now,
                    f'{self._machine.name} failed from wear and tear degradation.')

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

