import copy

from . import EventType
from ..utils import assert_is_instance


class ResourceManager:
    '''Provides pools of limited resources which can be reserved by
    callers and released back.

    An attempt to reserve resources can be made immediately or a
    callback function to be registered to be invoked when the requested
    resources are available.
    '''

    def __init__(self):
        # Dictionary: {resource name: (current use, maximum)}
        self._resources = {}
        self._waiting_requests = []
        self._env = None
        self._name = f'{type(self).__name__}'

    def initialize(self, env):
        '''Prepare ResourceManager for simulation.

        Called when simulation starts for the first time.

        Arguments
        ---------
        env: Environment
            Environment used in the simulation.
        '''
        self._env = env
        # Record initial resource amounts.
        for resource_name in self._resources.keys():
            self._record_resource_amount_update(resource_name)

    def get_resource_usage(self, resource_name):
        '''Get how much of a resource is currently reserved/in-use.

        Arguments
        ---------
        resource_name: str
            Resource type identifier.

        Returns
        -------
        float
            How much of the specified resource is currently reserved.
        '''
        try:
            return self._resources[resource_name][0]
        except KeyError:
            return 0.0

    def get_resource_capacity(self, resource_name):
        '''Get total capacity of a resource (reserved + unreserved).

        Arguments
        ---------
        resource_name: str
            Resource type identifier.

        Returns
        -------
        float
            What is the total amount of the specified resource, this
            includes both reserved and unreserved resources.
        '''
        try:
            return self._resources[resource_name][1]
        except KeyError:
            return 0.0

    def add_resources(self, resource_name, amount):
        '''Add or reduce maximum resource capacity.

        Note
        ----
        Reducing resource capacity below current usage will not force
        those resources to be released therefore allowing resource
        usage to remain above the new maximum.

        Arguments
        ---------
        resource_name: str
            Resource type identifier.
        amount: int, float
            How much of the specified resource type to add. If the value
            is negative then then maximum pool of that resource will be
            reduced.

        Raises
        ------
        ValueError
            When trying to reduce a resource by more than the maximum
            capacity of that resource.
        '''
        assert type(resource_name) == str, 'Resource identifier must be a string.'
        if amount == 0:
            return
        else:
            try:
                in_use, max_available = self._resources[resource_name]
                if amount < 0 and max_available + amount < 0:
                    raise ValueError(f'Cannot reduce amount of available resource {resource_name}'
                                     +' below zero.')
                self._resources[resource_name] = (in_use, max_available + amount)
            except KeyError:
                self._resources[resource_name] = (0.0, amount)

        if self._env != None:
            self._record_resource_amount_update(resource_name)
            self._schedule_check_pending_requesters()

    def reserve_resources(self, request):
        '''Try to reserve one or more types of resources.

        If the entire request cannot be completed then no resources will
        be reserved.

        Arguments
        ---------
        request: Dictionary
            A dictionary where each entry specifies what resource is
            requested and an amount requested that is >= 0. For example:
            {'resourceA': 10, 'resourceB': 1}

        Returns
        -------
        ReservedResources
            ReservedResources with reserved resources if successful.
            Returns None if the request could not be fulfilled.
        '''
        filtered_request = {name: n for name, n in request.items() if n > 0}
        if self._can_fulfill_request(filtered_request):
            # Reduce pools of available resources.
            for resource_name, amount in request.items():
                if amount == 0:
                    continue
                if amount < 0:
                    raise ValueError(f'Requested amount for {resource_name} is less than 0.')
                in_use, max_available = self._resources[resource_name]
                self._resources[resource_name] = (in_use + amount, max_available)
                self._record_resource_amount_update(resource_name)
            return ReservedResources(self, filtered_request)
        else:
            return None

    def reserve_resources_with_callback(self, request, callback):
        '''Register a callback function to be invoked when the request
        can be fulfilled.

        Resources will not be automatically reserved when the callback
        is invoked. The caller can use the reserve_resources function
        within the callback to immediately reserve those resources.

        Arguments
        ---------
        request: Dictionary
            A Dictionary where each entry specifies what resource is
            requested and the amount requested, resource_name:amount.
        callback: function(resource_manager, request)
            Function to be invoked when there are sufficient available
            resources to fulfill the request.
            The callback needs to accept two parameter:
            - the resource manager
            - copy of the request Dictionary
        '''
        self._waiting_requests.append((copy.deepcopy(request), callback))
        self._schedule_check_pending_requesters()

    def _schedule_check_pending_requesters(self):
        self._env.schedule_event(self._env.now, -1, self._check_pending_requests,
                                 EventType.OTHER_HIGH_PRIORITY, 'From ResourceManager')

    def _check_pending_requests(self):
        i = 0
        while i < len(self._waiting_requests):
            if self._can_fulfill_request(self._waiting_requests[i][0]):
                self._waiting_requests[i][1](self, self._waiting_requests[i][0])
                self._waiting_requests.pop(i)
            else:
                i += 1

    def _release_resources(self, resources):
        for resource_name, amount in resources.items():
            if amount == 0:
                continue
            in_use, max_available = self._resources[resource_name]
            self._resources[resource_name] = (in_use - amount, max_available)
            self._record_resource_amount_update(resource_name)
        self._schedule_check_pending_requesters()

    def _can_fulfill_request(self, request):
        for resource_name, requested_amount in request.items():
            if requested_amount == 0:
                continue
            try:
                in_use, max_available = self._resources[resource_name]
                if max_available - in_use < requested_amount:
                    return False
            except KeyError:
                return False
        return True

    def _record_resource_amount_update(self, resource_name):
        in_use, max_available = self._resources[resource_name]
        self._env.add_datapoint('resource_update', resource_name, (self._env.now, in_use, max_available))


class ReservedResources():
    '''Tracks reserved resources from a request.

    Use .release() function to release the reserved resources tracked by
    this ReservedResources instance.
    '''

    def __init__(self, resource_manager, reserved_resources):
        self._resource_manager = resource_manager
        self._reserved_resources = reserved_resources

    @property
    def reserved_resources(self):
        '''Dictionary of the resources reserved and their amounts.
        '''
        return copy.deepcopy(self._reserved_resources)

    def release(self, resources = None):
        '''Release resources back into the pool of available resources.

        Arguments
        ---------
        resources: Dictionary, default=None
            A Dictionary where each entry specifies what resource to
            release and an amount to be released that is >= 0.
            For example: {'resourceA': 10, 'resourceB': 1}
            If None then it will release all the resources reserved here.

        Raises
        ------
        ValueError
            If trying to release an amount of a resources that is more
            than is still reserved or trying to release a negative
            amount of a resource.
        '''
        if resources == None:
            resources = self._reserved_resources
        else:
            # If resources to release were specified then ensure that
            # sufficient resources are reserved.
            for resource_name, amount in resources.items():
                if amount < 0:
                    raise ValueError(f'Trying to release a negative amount of {resource_name}')
                try:
                    if amount != 0 and self._reserved_resources[resource_name] < amount:
                        raise ValueError(f'Trying to release {amount} of {resource_name} but only ' + \
                                        f'{self._reserved_resources[resource_name]} is reserved.')
                except KeyError:
                    raise KeyError(f'This request did not reserve any {resource_name}')

        self._resource_manager._release_resources(resources)
        # Reduce reserved resources by amounts released.
        to_delete = []
        for resource_name, amount in resources.items():
            if amount > 0:
                self._reserved_resources[resource_name] -= amount
            if self._reserved_resources[resource_name] == 0:
                to_delete.append(resource_name)
        # Remove from the dictionary of reserved resources any resource
        # pool that reaches 0..
        for resource_name in to_delete:
            del self._reserved_resources[resource_name]

    def merge(self, reserved_resources):
        '''Merge the resources reserved by another ReservedResources
        object into this one.

        Arguments
        ---------
        reserved_resources: ReservedResources
            ReservedResources object whose reserved resources will be
            merged into this. The provided reserved_resources object
            will be set to have no reserve resources.
        '''
        assert_is_instance(reserved_resources, ReservedResources)
        for resource_name, amount in reserved_resources._reserved_resources.items():
            try:
                self._reserved_resources[resource_name] += amount
            except KeyError:
                self._reserved_resources[resource_name] = amount
        reserved_resources._reserved_resources = {}

    def __del__(self):
        if (self._resource_manager._env.is_simulation_in_progress()
            and len(self._reserved_resources)) > 0:
            print('ReservedResources was deleted before all resources'
                  +f' were released: {self._reserved_resources}')

