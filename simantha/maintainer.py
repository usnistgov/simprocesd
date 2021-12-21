# import random

from .simulation import EventType
from .components.asset import Asset


class MaintenanceRequest:

    def __init__(self, machine, failure_name, time_to_fix, request_capacity):
        self.machine = machine
        self.failure_name = failure_name
        self.time_to_fix = time_to_fix
        self.request_capacity = request_capacity


class Maintainer(Asset):
    '''
    A maintainer is responsible for repairing machines that request maintenance.
    '''

    def __init__(self,
                 name = 'maintainer',
                 capacity = float('inf'),
                 cost_per_interval = (0, 0),  # cost, interval
                 ** kwargs):
        super().__init__(name, **kwargs)

        self._capacity = capacity
        self._utilization = 0
        self._env = None
        self._request_queue = []
        self._cost_per_interval = cost_per_interval

    def initialize(self, env):
        super().initialize(env)

        # Interval of 0 or less means no periodic cost..
        if self._cost_per_interval[1] > 0:
            self._incur_cost()

    def request_maintenance(self, machine, failure_name):
        print(f'requesting maintenance {failure_name}')
        machine_failure = machine.machine_status.possible_failures[failure_name]
        assert machine_failure != None, f'{failure_name} is not a failure in {machine.name}'
        self._request_queue.append(
            MaintenanceRequest(machine_failure.machine,
                               machine_failure.name,
                               machine_failure.get_time_to_repair(),
                               machine_failure.capacity_to_repair))
        self.try_working_requests()

    def try_working_requests(self):
        i = 0
        while i < len(self._request_queue):
            req = self._request_queue[i]
            if self._utilization < self._capacity + req.request_capacity:
                self._request_queue.pop(i)

                self._utilization += req.request_capacity
                self._env.schedule_event(
                    self._env.now,
                    self.id,
                    lambda: self._shutdown_and_repair(req),
                    EventType.RESTORE,
                    f'shutting down before repair: {req.machine.name}')
            else:
                i += 1

    def _shutdown_and_repair(self, request):
        print(f'start working request {request.failure_name}')
        request.machine.shutdown()
        # Begin fixing
        self._env.schedule_event(
            self._env.now + request.time_to_fix,
            self.id,
            lambda: self._restore_machine(request),
            EventType.RESTORE,
            f'Repairing: {request.machine.name}')

    def _incur_cost(self):
        self.value -= self._cost_per_interval[0]
        self._schedule_next_cost()

    def _schedule_next_cost(self):
        self._env.schedule_event(
            self._env.now + self._cost_per_interval[1],
            self.id,
            self._incur_cost,
            EventType.OTHER_HIGH
        )

    def _restore_machine(self, request):
        print(f'restoring: {request.failure_name}')
        request.machine.fix_failure(request.failure_name)
        request.machine.restore_functionality()
        self._utilization -= request.request_capacity

        self.try_working_requests()

