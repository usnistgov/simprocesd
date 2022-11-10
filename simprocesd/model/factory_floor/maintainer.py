from ...utils import assert_is_instance
from ..simulation import EventType
from .asset import Asset


class Maintainable:
    ''' Maintainable represents an interface for Maintainer to create,
    prioritize, and execute work orders on any class that extends
    Maintainable.
    '''

    @property
    def name(self):
        return ''

    def get_work_order_duration(self, tag):
        ''' Returns how long it will take to perform the work order
        indicated by the tag.
        Duration is measured in simulation time units.

        Arguments:
        tag -- identifier for the work order.
        '''
        return 0

    def get_work_order_capacity(self, tag):
        ''' Returns how much of the maintainer's capacity is needed to
        perform the work order indicated by the tag.

        Arguments:
        tag -- identifier for the work order.
        '''
        return 0

    def get_work_order_cost(self, tag):
        ''' Returns the one time cost to maintainer to perform the
        work order indicated by the tag. If work order cost is tracked
        elsewhere then this should return 0 (default implementation).

        Arguments:
        tag -- identifier for the work order.
        '''
        return 0

    def start_work(self, tag):
        ''' Called by a maintainer when it begins working on the work
        order.

        Arguments:
        tag -- identifier for the work order.
        '''
        pass

    def end_work(self, tag):
        ''' Called by a maintainer when it finished working on the
        work order.

        Arguments:
        tag -- identifier for the work order.
        '''
        pass


class WorkOrder:

    def __init__(self, target, tag, needed_capacity):
        assert_is_instance(target, Maintainable)
        self.target = target
        self.tag = tag
        self.needed_capacity = needed_capacity


class Maintainer(Asset):
    '''
    A maintainer is responsible for performing requested work orders.
    Requests are generally worked in a first come first serve order
    but a later request may be worked first when available capacity is
    insufficient for the earlier request.

    Arguments:
    name -- name of the maintainer.
    capacity -- capacity of the maintainer. Units are not defined but
        need to be consistent with work order capacity requirements.
    value -- starting value/cost of the maintainer.
    '''

    def __init__(self, name = 'maintainer', capacity = float('inf'), value = 0):
        super().__init__(name, value)

        self._capacity = capacity
        self._utilization = 0
        self._env = None
        self._request_queue = []
        self._active_requests = []

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
        self._utilization = 0
        self._request_queue = []
        self._active_requests = []

    def create_work_order(self, target, tag = None):
        ''' Create a new work order and add it to the queue with other
        work order requests, see class description for details on the
        queue.

        Arguments:
        target -- Item which will receive maintenance. Has to  be of
            type Maintainable.
        tag -- work order identifier used by target to determine
            what work is going to be performed. Tag supports any
            object type.

        Returns: True if the work order was added to the queue and
        False if it was rejected. Request will be rejected if the same
        work order request is already in the queue or if such an order
        is already being worked on.
        '''
        if self._is_work_order_requested(target, tag):
            return False

        capacity = target.get_work_order_capacity(tag)
        self._env.add_datapoint('enter_queue', self.name,
                                (self._env.now, target.name, tag))
        self._request_queue.append(WorkOrder(target, tag, capacity))
        self.try_working_requests()
        return True

    def _is_work_order_requested(self, target, tag = None):
        for r in self._request_queue:
            if r.target == target and r.tag == tag:
                return True
        for r in self._active_requests:
            if r.target == target and r.tag == tag:
                return True
        return False

    def try_working_requests(self):
        ''' Maintainer will look through available work orders and
        attempt to work as many of them as possible for the available
        capacity.
        This function is called automatically when requests are made
        and when requests are completed.
        '''
        i = 0
        while i < len(self._request_queue):
            req = self._request_queue[i]
            if self._utilization <= self._capacity - req.needed_capacity:
                self._request_queue.pop(i)
                self._active_requests.append(req)

                self._utilization += req.needed_capacity
                self._env.schedule_event(
                    self._env.now,
                    self.id,
                    lambda r = req: self._start_work_order(r),
                    EventType.START_WORK,
                    f'start work order: {req.target.name}')
            else:
                i += 1

    def _start_work_order(self, request):
        ttm = request.target.get_work_order_duration(request.tag)
        self._env.add_datapoint('start_work_order', self.name,
                                (self._env.now, request.target.name, request.tag))

        cost = request.target.get_work_order_cost(request.tag)
        self.add_cost(f'work order - tag:{request.tag} target:{request.target.name}', cost)

        request.target.start_work(request.tag)
        self._env.schedule_event(
            self._env.now + ttm,
            self.id,
            lambda r = request: self._finish_work_order(r),
            EventType.FINISH_WORK,
            f'end work order: {request.target.name}')

    def _finish_work_order(self, request):
        request.target.end_work(request.tag)
        self._utilization -= request.needed_capacity
        self._active_requests.remove(request)
        self._env.add_datapoint('finish_work_order', self.name,
                                (self._env.now, request.target.name, request.tag))

        self.try_working_requests()

