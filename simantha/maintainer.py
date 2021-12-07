# import random

from .simulation import EventType


class MaintenanceRequest:

    def __init__(self, machine, request_capacity):
        self.machine = machine
        self.request_capacity = request_capacity


class Maintainer:
    '''
    A maintainer is responsible for repairing machines that request maintenance.
    '''

    def __init__(self, name = 'maintainer', capacity = float('inf')):
        self.name = name
        self._capacity = capacity

        self._utilization = 0
        self._env = None
        self._request_queue = []

    def initialize(self, env):
        self._env = env

    def request_maintenance(self, machine, request_capacity = 1):
        self._request_queue.append(MaintenanceRequest(machine, request_capacity))
        self.try_working_requests()

    def try_working_requests(self):
        i = 0
        while i < len(self._request_queue):
            req = self._request_queue[i]
            if self._utilization < self._capacity + req.request_capacity:
                self._request_queue.pop(i)

                self._utilization += req.request_capacity
                # Begin fixing
                self._env.schedule_event(
                    self._env.now + req.machine.machine_status.time_to_fix,
                    req.machine.id,
                    lambda: self._restore_machine(req),
                    EventType.RESTORE)
            else:
                i += 1

    def _restore_machine(self, request):
        request.machine.restore_functionality()
        self._utilization -= request.request_capacity

        self.try_working_requests()

