from ..simulation import EventType
from .asset import Asset


class MaintenanceRequest:

    def __init__(self, machine, maintenance_tag, request_capacity):
        self.machine = machine
        self.maintenance_tag = maintenance_tag
        self.request_capacity = request_capacity


class Maintainer(Asset):
    '''
    A maintainer is responsible for repairing machines after maintenance
    was requested.
    Requests are generally worked in a first in first out order. A later
    request may be worked first when available capacity is insufficient
    for the earlier request.

    Arguments:
    name -- name of the maintainer.
    capacity -- capacity of the maintainer. Units need to be consistent
        with MachineStatusTracker.get_capacity_to_maintain.
    cost_per_period -- (cost, period) set if the maintainer has a
        periodic cost. Maintainer will incur the cost at the beginning
        of every period.
    value -- initial value/cost of the maintainer.
    '''

    def __init__(self, name = 'maintainer', capacity = float('inf'), cost_per_period = (0, 0),
                 value = 0):
        super().__init__(name, value)

        self._capacity = capacity
        self._utilization = 0
        self._env = None
        self._request_queue = []
        self._active_requests = []
        assert cost_per_period[0] == 0 or cost_per_period[1] > 0, \
                'Period cannot be 0 if cost is not 0.'
        self._cost_per_period = cost_per_period

    @property
    def total_capacity(self):
        ''' Maximum capacity of the maintainer.
        '''
        return self._capacity

    @property
    def available_capacity(self):
        ''' Currently available capacity of the Maintainer.
        '''
        return self._capacity - self._utilization

    def initialize(self, env):
        super().initialize(env)
        # Cost of 0 means there is no need to schedule a recurring cost.
        if self._cost_per_period[0] != 0:
            self._add_periodic_cost()

    def request_maintenance(self, machine, maintenance_tag = None):
        ''' Enter maintenance request into the queue, see class
        description for more details on the queue.
        Returns True if request was added to the queue and False if it
        was rejected. Request will be rejected if the same request is
        already in the queue or is already being worked.

        Arguments:
        machine -- Machine which will receive maintenance.
        maintenance_tag -- maintenance tag used by machine to determine
            what maintenance is going to be performed. Supports any
            object type.
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
        ''' Maintainer will look through available requests and attempt
        to work them if capacity allows. Is called automatically when
        requests are made and when requests are completed.
        '''
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

    def _restore_machine(self, request):
        request.machine.status_tracker.maintain(request.maintenance_tag)
        request.machine.restore_functionality()
        self._utilization -= request.request_capacity
        self._active_requests.remove(request)
        self._env.add_datapoint('finish_maintenance', self.name,
                                (self._env.now, request.machine.name, request.maintenance_tag))

        self.try_working_requests()

    def _add_periodic_cost(self):
        self.add_cost('maintainer_periodic_expense', self._cost_per_period[0])
        self._schedule_next_periodic_cost()

    def _schedule_next_periodic_cost(self):
        self._env.schedule_event(
            self._env.now + self._cost_per_period[1],
            self.id,
            self._add_periodic_cost,
            EventType.OTHER_HIGH,
            f'{self.name} periodic cost.'
        )
