from ...utils import assert_is_instance
from ..simulation import EventType
from .asset import Asset


class Maintainable:
    '''An interface the Maintainer uses to create, prioritize, and
    execute work orders.

    Maintainer can only perform work orders on classes that use
    Maintainable as one of their base classes.
    '''

    def get_work_order_duration(self, tag):
        '''Called at the beginning of performing a work order to
        determine how long the work order will take.

        Arguments
        ---------
        tag: object
            Identifier for the work order.

        Returns
        -------
        float
            How long it will take to perform the work order indicated
            by the tag. Duration is measured in simulation time units.
        '''
        return 0

    def get_work_order_capacity(self, tag):
        ''' Called once when the work order is created to determine how
        much of the Maintainer's capacity is needed to perform the work
        order.

        Arguments
        ---------
        tag: object
            Identifier for the work order.

        Returns
        -------
        float
            Needed capacity to perform the work order indicated by the
            tag.
        '''
        return 0

    def get_work_order_cost(self, tag):
        ''' Called once to get the cost to Maintainer to perform the
        work order.

        Returned value will be subtracted from Maintainer's value. If
        the work order cost is tracked elsewhere then this should return
        0 (default implementation).

        Arguments
        ---------
        tag: object
            Identifier for the work order.

        Returns
        -------
        float
            Needed capacity to perform the work order indicated by the
            tag.
        '''
        return 0

    def start_work(self, tag):
        ''' Called by Maintainer when it begins working on the work
        order.

        Arguments
        ---------
        tag: object
            Identifier for the work order.
        '''
        pass

    def end_work(self, tag):
        ''' Called by Maintainer when it finishes working on the work
        order.

        Arguments
        ---------
        tag: object
            Identifier for the work order.
        '''
        pass


class WorkOrder:

    def __init__(self, target, tag, needed_capacity):
        assert_is_instance(target, Maintainable)
        self.target = target
        self.tag = tag
        self.needed_capacity = needed_capacity


class Maintainer(Asset):
    '''Asset that is responsible for performing requested work orders.

    Requests are generally worked in a first come first serve order
    but a later request may be worked first when available capacity is
    insufficient for the earlier request.

    Maintainer can work on multiple work orders at the same time as long
    the the combined needed capacity of the work orders is less than or
    equal to the Maintainer's maximum capacity. Needed capacity is
    determined by Maintainable.get_work_order_capacity

    Note
    ----
    Capacity units are not defined but need to be consistent across work
    order capacity requirements and Maintainer's maximum capacity.

    Arguments
    ---------
    name: str, default=None
        Name of the Maintainer. If name is None then the Maintainer's
        name will be changed to Maintainer_<id>
    capacity: float, optional
        Maintainer's maximum capacity.
    value: float, default=0
        Starting value of the Asset.
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
        ''' How much of the Maintainer's capacity is currently not being
        used.
        '''
        return self._capacity - self._utilization

    def initialize(self, env):
        super().initialize(env)
        self._utilization = 0
        self._request_queue = []
        self._active_requests = []

    def create_work_order(self, target, tag = None):
        '''Request a new work order to be performed.

        Creates a new work order and adds it to the back of the queue of
        work orders to be executed.

        Arguments
        ---------
        target: Maintainable
            Target of the work order to be performed.
        tag: object, default=None
            Identifier the target uses to differentiate between various
            work orders that could be performed on it.

        Returns
        -------
        bool
            True if the work order was added to the queue and
            False if it was rejected. Request will be rejected if the
            same work order request is already in the queue or is being
            worked on.
        '''
        assert_is_instance(target, Maintainable)
        if self._is_work_order_requested(target, tag):
            return False

        capacity = target.get_work_order_capacity(tag)
        name = getattr(target, 'name', 'N/A')
        self._env.add_datapoint('enter_queue', self.name, (self._env.now, name, tag))
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
        '''Maintainer will look through the work order queue and
        attempt to start working on each one.

        Work orders will be started if the Maintainer has enough
        available capacity to perform that work order.

        Note
        ----
        This function is called automatically when requests are made
        and when requests are completed. Normally there should be no
        need to call it manually.
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

