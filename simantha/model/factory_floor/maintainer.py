from ..simulation import EventType
from .asset import Asset


class MaintenanceRequest:

    def __init__(self, machine, maintenance_tag, request_capacity):
        self.machine = machine
        self.maintenance_tag = maintenance_tag
        self.request_capacity = request_capacity


class Maintainer(Asset):
    '''
    A maintainer is responsible for repairing machines that request
    maintenance.
    Requests are generally worked in a first in first out order. A later
    request may be worked first when available capacity is insufficient
    for the earlier request but sufficient for the later request.
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
        self._active_requests = []
        self._cost_per_interval = cost_per_interval

    def initialize(self, env):
        super().initialize(env)

        # Interval of 0 or less means no periodic cost..
        if self._cost_per_interval[1] > 0:
            self._incur_periodic_expense()

    def request_maintenance(self, machine, maintenance_tag = None):
        ''' Enter maintenance request into the queue, see class
        description for more details on the queue.
        Returns True if request was added to the queue and False
        otherwise. Request may be skipped if the same request is already
        in the queue or is already being worked.
        '''
        if self._is_maintenance_requested(machine, maintenance_tag):
            return False

        capacity = machine.status_tracker.get_capacity_to_maintain(maintenance_tag)
        self._env.add_datapoint('enter_queue', self.name,
                                (self._env.now, machine.name, maintenance_tag))
        self._request_queue.append(
            MaintenanceRequest(machine, maintenance_tag, capacity))
        self.try_working_requests()
        return True

    def _is_maintenance_requested(self, machine, maintenance_tag = None):
        for r in self._request_queue:
            if r.machine == machine and r.maintenance_tag == maintenance_tag:
                return True
        for r in self._active_requests:
            if r.machine == machine and r.maintenance_tag == maintenance_tag:
                return True
        return False

    def try_working_requests(self):
        i = 0
        while i < len(self._request_queue):
            req = self._request_queue[i]
            if self._utilization <= self._capacity - req.request_capacity:
                self._request_queue.pop(i)
                self._active_requests.append(req)

                self._utilization += req.request_capacity
                self._env.schedule_event(
                    self._env.now,
                    self.id,
                    lambda: self._shutdown_and_repair(req),
                    EventType.OTHER_LOW,
                    f'shutting down before repair: {req.machine.name}')
            else:
                i += 1

    def _shutdown_and_repair(self, request):
        ttm = request.machine.status_tracker.get_time_to_maintain(request.maintenance_tag)
        self._env.add_datapoint('begin_maintenance', self.name,
                                (self._env.now, request.machine.name, request.maintenance_tag))
        request.machine.shutdown()
        # Begin fixing
        self._env.schedule_event(
            self._env.now + ttm,
            self.id,
            lambda: self._restore_machine(request),
            EventType.RESTORE,
            f'Repairing: {request.machine.name}')

    def _add_periodic_cost(self):
        self.add_cost('maintainer_periodic_expense', self._cost_per_interval[0])
        self._schedule_next_periodic_cost()

    def _schedule_next_periodic_cost(self):
        self._env.schedule_event(
            self._env.now + self._cost_per_interval[1],
            self.id,
            self._add_periodic_cost,
            EventType.OTHER_HIGH
        )

    def _restore_machine(self, request):
        request.machine.status_tracker.maintain(request.maintenance_tag)
        request.machine.restore_functionality()
        self._utilization -= request.request_capacity
        self._active_requests.remove(request)
        self._env.add_datapoint('finish_maintenance', self.name,
                                (self._env.now, request.machine.name, request.maintenance_tag))

        self.try_working_requests()

