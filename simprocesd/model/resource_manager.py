import copy

from . import EventType


class ResourceManager:
    '''Provides a pool of limited resources which can be reserved by
    callers and released back to the resource pool.

    Callers can try to reserve resources immediately or they can provide
    a callback function to be invoked when the requested resources are
    available.
    '''

    def __init__(self):
        self._resources = {}
        self._waiting_requests = []
        self._env = None
        self._name = f'{type(self).__name__}'
        self._init_count = 0

    @property
    def available_resources(self):
        '''Return a dictionary of unreserved resources.
        '''
        return copy.deepcopy(self._resources)

    def initialize(self, env):
        '''Prepare ResourceManager for simulation and reset attributes
        to starting values.

        Called when simulation starts for the first time or when it is
        restarted.

        Arguments
        ---------
        env: Environment
            Environment used in the simulation.
        '''
        if self._env == None:
            # Initializing for the first time, save starting parameters.
            self._initial_resources = copy.deepcopy(self._resources)
            self._env = env
        else:
            # Simulation is resetting, restore starting resources.
            self._resources = copy.deepcopy(self._initial_resources)

        # Record initial resource amounts.
        for resource_name, amount in self._resources.items():
            self._record_resource_amount_update(resource_name)

        self._init_count += 1

    def add_resources(self, resource_name, amount):
        '''Add new unreserved resources or reduce the pool of available
        resources.

        Arguments
        ---------
        resource_name: str
            Resource type identifier.
        amount: float
            How much of the specified resource type to add or remove if
            the value is negative.

        Raises
        ------
        ValueError
            When trying to release more of a resource than is currently
            unreserved.
        '''
        if amount == 0:
            return
        elif amount > 0:
            try:
                self._resources[resource_name] += amount
            except KeyError:
                self._resources[resource_name] = amount
        else:  # amount < 0
            if self._resources[resource_name] < -amount:
                raise ValueError(f'Cannot reduce amount of available resource {resource_name}'
                                 +' below zero.')
            self._resources[resource_name] -= amount

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
            requested and the amount requested, resource_name:amount.

        Returns
        -------
        ReservedResources with requested resources if successful.
        Calling .release() on the returned object will make the reserved
        resources available again.
        Returns None if requested resources could not be reserved.
        '''
        if self._can_fulfill_request(request):
            # Reduce pools of available resources.
            for resource_name, amount in request.items():
                self._resources[resource_name] -= amount
                self._record_resource_amount_update(resource_name)
            return ReservedResources(self, copy.deepcopy(request))
        else:
            return None

    def reserve_resources_with_callback(self, request, callback):
        '''Set the callback function to be called when the request can
        be fulfilled.

        The caller can use .reserve_resources within the callback to
        ensure that the available resources are not reserved elsewhere.

        Arguments
        ---------
        request: Dictionary
            A Dictionary where each entry specifies what resource is
            requested and the amount requested, resource_name:amount.
        callback: function
            Function to be invoked when there are sufficient available
            resources to fulfill the request.
            The functions needs to accept one parameter which will be
            the copy of the request.
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
                self._waiting_requests[i][1](self._waiting_requests[i][0])
                self._waiting_requests.pop(i)
            else:
                i += 1

    def _release_resources(self, resources):
        for resource_name, amount in resources.items():
            self._resources[resource_name] += amount
            self._record_resource_amount_update(resource_name)
        self._schedule_check_pending_requesters()

    def _can_fulfill_request(self, request):
        for resource_name, amount in request.items():
            try:
                if self._resources[resource_name] < amount:
                    return False
            except KeyError:
                return False
        return True

    def _record_resource_amount_update(self, resource_name):
        self._env.add_datapoint('resource_update', resource_name,
                                (self._env.now, self._resources[resource_name]))


class ReservedResources():
    '''Tracks reserved resources from a request.

    Use .release() function to release all reserved resources tracked by
    this ReservedResources instance.
    '''

    def __init__(self, resource_manager, reserved_resources):
        self._resource_manager = resource_manager
        self._reserved_resources = reserved_resources
        self._init_count_when_made = self._resource_manager._init_count

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
            release and the amount to be released, resource_name:amount
            If None then it will release all the resources reserved here.

        Raises
        ------
        ValueError
            If trying to release an amount of a resources that is more
            than is still reserved.
        RuntimeError
            When trying to release resources after the simulation was
            reset.
        '''
        if self._init_count_when_made != self._resource_manager._init_count:
            raise RuntimeError('Trying to release resources that were reserved before the simulation'
                               +'was reset.')

        if resources == None:
            resources = self._reserved_resources
        else:
            # If resources to release were specified then ensure that
            # sufficient resources are reserved.
            for resource_name, amount in resources.items():
                if self._reserved_resources[resource_name] < amount:
                    raise ValueError(f'Trying to release {amount} of {resource_name} but only ' + \
                                    f'{self._reserved_resources[resource_name]} is reserved.')

        self._resource_manager._release_resources(resources)
        # Reduce reserved resources by amounts released.
        for resource_name, amount in resources.items():
            self._reserved_resources[resource_name] -= amount

    def __del__(self):
        if (self._init_count_when_made != self._resource_manager._init_count
            or not self._resource_manager._env.is_simulation_in_progress()):
            # Simulation is over or it has been reset since the
            # resources were reserved.
            return
        for resource_name, amount in self._reserved_resources.items():
            if amount != 0:
                print(f'WARNING: ReservedResources was deleted/GCed before releasing it\'s resources:')
                print(f'\t{self._reserved_resources}')
                return

