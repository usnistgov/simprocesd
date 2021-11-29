import random
import warnings

from .asset import Asset
from .simulation import *

class Machine(Asset):
    """
    Machine that processes parts with optional periodic degradation and failure.

    Parameters
    ----------
    name : str
        Name of the machine.
    cycle_time : int or simantha.Distribution
        Cycle time in time units for each part processed by this machine.
    degradation_matrix : square array
        Markovian degradation transition matrix.
    cbm_threshold : int
        Threshold for condition-based preventive maintenance. 
    pm_distribution : int or simantha.Distribution
        Time to repair distribution for preventive maintenance.
    cm_distribution : int or simantha.Distribution
        Time to repair distribution for corrective maintenance.

    
    Methods
    -------
    define_routing(upstream=[], downstream=[])
        Specifies the upstream and downstream objects of the machine. The ``upstream`` 
        and ``downstream`` arguments should be lists containing source, buffer, or sink
        objects. 


    .. warning:: 
        Machines should be adjacent to sources, buffers, or sinks. Behavior of adjacent
        machines with no intermediate buffer is not tested and may result in errors or
        unexpected results.


    The following methods may be overridden by extensions of the ``Machine`` class.


    Methods
    -------
    initialize_addon_process()
        Called when the machine is initialized at the beginning of each simulation run.
    output_addon_process(part)
        Called before the processed part is transfered to a downstream buffer or sink.
    repair_addon_process()
        Called once a machine is restored after preventive or corrective maintenance.


    The following attributes are used to indicate the state of a machine.

    Attributes
    ----------
    has_part : bool
        ``True`` if the machine is holding a part, ``False`` otherwise. Simantha uses 
        the *block after service* convention wherein a machine will hold a part after
        processing until space for the processed part is available.
    under_repair : bool
        ``True`` if the machine is undergoing maintenance, ``False`` otherwise. 
    in_queue : bool
        ``True`` if the machine has requested unfulfilled (preventive or 
        corrective) maintenance, ``False`` otherwise. 


    During simulation, machines collect the following data that are available as 
    attributes of a ``Machine`` instance.


    Attributes
    ----------
    parts_made : int
        The number of parts successfully processed and relinquished by the machine.
    downtime : int
        The number of time units the machine was either under maintenance or failed. 
    production_data : dict
        Production information of the machine. ``production_data['time']`` stores the 
        time at which each part exited the machine while 
        ``production_data['production']`` stores the cumulative number of parts produced 
        by the machine at the corresponding time. 
    health_data : dict
        A dictionary storing the health infomation of the machine with keys ``time`` and
        ``health`` and values corresponding to the time of each health state transition
        and the resulting health of the machine. Machines that are not subject to 
        degradation do not undergo health state transitions and remain in perfect health
        for the duration of the simulation. 
    maintenance_data : dict
        Serves as a maintenance log for the machine. Key ``'event'`` gives a list of 
        maintenance events which can include ``'enter queue'``, ``'failure'``, 
        ``'begin maintenance'``, or ``'restore'``, while key ``'time'`` gives the
        simulation time of each event. 

    """
    def __init__(
        self,
        name=None,
        cycle_time=1,
        selection_priority=1,

        degradation_matrix=[[1,0],[0,1]], # By default, never degrade
        cbm_threshold=None,
        planned_failure=None, # Optional planned failure, in the form of
                              # (time, duration)

        pm_distribution=5,
        cm_distribution=10,
        
        # Initial machine state
        initial_health=0,
        initial_remaining_process=None
    ):
        # User-specified parameters
        self.name = name
        
        self.cycle_time = Distribution(cycle_time)
        
        if initial_remaining_process is not None:
            self.initial_remaining_process = initial_remaining_process
        else:
            self.initial_remaining_process = self.get_cycle_time()
        self.remaining_process_time = self.initial_remaining_process
        self.selection_priority = selection_priority
        
        # Initial machine state
        self.has_finished_part = False
        self.initial_health = initial_health
        self.health = initial_health
        self.degradation_matrix = degradation_matrix
        self.failed_health = len(degradation_matrix) - 1
        self.cbm_threshold = cbm_threshold or self.failed_health # If not specified, CM is used
        if self.health == self.failed_health:
            self.failed = True
        else:
            self.failed = False
        self.assigned_maintenance = False
        self.maintainer = None
        self.has_reserved_part = False

        self.pm_distribution = Distribution(pm_distribution)
        self.cm_distribution = Distribution(cm_distribution)

        self.planned_failure = planned_failure

        # Check if planned failures and degradation are specified (may cause errors)
        if planned_failure is not None and degradation_matrix[0][0] != 1:
            warnings.warn(
                'Specifying planned failures along with degradation is untested and may cause errors.'
            )
        
        # Routing
        self.upstream = []
        self.downstream = []
        
        # Machine status
        self.has_part = False
        self.under_repair = False
        self.in_queue = False
        self.remaining_ttr = None
    
        # Machine statistics
        self.parts_made = 0
        self.downtime = 0

        # Simulation data
        self.production_data = {'time': [0], 'production': [0]}
        self.health_data = {'time': [0], 'health': [self.health]}
        self.maintenance_data = {'time': [], 'event': []}
        
        self.env = None

    def initialize(self):
        self.remaining_process_time = self.initial_remaining_process
        self.health = self.initial_health
        if self.health == self.failed_health:
            self.failed = True
        else:
            self.failed = False
        self.time_entered_queue = -1

        self.has_part = False
        self.under_repair = False
        self.in_queue = False
        self.remaining_ttr = None

        self.target_giver = None
        self.target_receiver = None

        self.reserved_content = 0
        self.reserved_vacancy = 0
        self.contents = []

        self.blocked = False
        self.starved = True
        
        # Initialize statistics
        self.parts_made = 0
        self.downtime = 0

        # Schedule planned failures
        if self.planned_failure is not None:
            self.env.schedule_event(
                self.planned_failure[0], self, self.maintain_planned_failure
            )

        # Initialize data
        if self.env.collect_data:
            self.production_data = {'time': [0], 'production': [0]}
            self.health_data = {'time': [0], 'health': [self.health]}
            self.maintenance_data = {'time': [], 'event': []}

        # Schedule initial events
        time_to_degrade = self.get_time_to_degrade()
        self.env.schedule_event(
            time_to_degrade, self.name, self.degrade, f'{self.name}.initialize'
        )

        self.initialize_addon_process()

    def initialize_addon_process(self):
        """
        Called when the machine is initialized at the beginning of each simulation run.
        """
        pass
    
    def reserve_vacancy(self, quantity=1.):
        """
        Reserve available space at this machine. 
        """
        self.reserved_vacancy += quantity

    def get_part(self):
        """
        Choose a random upstream container from which to take a part.
        """
        assert self.target_giver is not None, f'No giver identified for {self.name}'
        
        # Get part from selected giver
        current_part = self.target_giver.get(1)
        self.contents.append(current_part)
        current_part.routing_history.append(self.name)

        self.has_part = True

        # Schedule a future request for space 
        self.env.schedule_event(
            self.env.now+self.get_cycle_time(),
            self.name, 
            self.request_space, 
            f'{self.name}.get_part at {self.env.now}'
        )

        # Check if this event unblocked another machine
        for asset in self.target_giver.upstream:
            if asset.can_give() and self.target_giver.can_receive():
                source = f'{self.name}.get_part at {self.env.now}'
                self.env.schedule_event(
                    self.env.now, asset, asset.request_space, source
                )

        self.target_giver = None

    def request_space(self):
        """
        Find available space for a finished part, request that space if found.
        """
        self.has_finished_part = True
        candidate_receivers = [obj for obj in self.downstream if obj.can_receive()]
        if len(candidate_receivers) > 0:
            self.target_receiver = random.choice(candidate_receivers)
            self.target_receiver.reserve_vacancy(1)
            source = f'{self.name}.request_space at {self.env.now}'
            self.env.schedule_event(self.env.now, self.name, self.put_part, source)
        else:
            self.blocked = True
            
    def put_part(self):
        """
        Place a finished part in available downstream vacancy. 
        """
        assert self.target_receiver is not None, f'No receiver identified for {self.name}'

        finished_part = self.contents.pop(0)

        self.output_addon_process(finished_part)

        self.target_receiver.put(finished_part, 1)

        self.blocked = False

        if self.env.now > self.env.warm_up_time:
            self.parts_made += 1
        self.has_finished_part = False
        self.has_part = False

        if self.env.now > self.env.warm_up_time and self.env.collect_data:
            self.production_data['time'].append(self.env.now)
            self.production_data['production'].append(self.parts_made)        

        source = f'{self.name}.put_part at {self.env.now}'
        self.env.schedule_event(self.env.now, self.name, self.request_part, source)
        
        self.target_receiver = None

    def output_addon_process(self, part):
        """
        Called before the part is transfered downstream. 
        """
        pass

    def request_part(self):
        """
        Search for available parts upstream, request part if found. 
        """
        candidate_givers = [obj for obj in self.upstream if obj.can_give()]
        if len(candidate_givers) > 0:
            self.starved = False
            self.target_giver = random.choice(candidate_givers)
            self.target_giver.reserve_content(1)
            source = f'{self.name}.request_part at {self.env.now}'
            self.env.schedule_event(self.env.now, self, self.get_part, source)
        else:
            self.starved = True

    def put(self, part, quantity=1.):
        """
        Put a part into available space at this machine. 
        """
        self.contents.append(part)
        part.routing_history.append(self.name)

        self.has_part = True

        self.env.schedule_event(
            self.env.now+self.get_cycle_time(),
            self.name, 
            self.request_space, 
            f'{self.name}.get_part at {self.env.now}'
        )

    def degrade(self):
        """
        Degrade by one unit and schedule a future degradation event. 
        """
        source = f'{self.name}.degrade at {self.env.now}'
        self.health += 1

        if self.env.collect_data:
            self.health_data['time'].append(self.env.now)
            self.health_data['health'].append(self.health)

        time_to_degrade = self.get_time_to_degrade()
        if self.health == self.failed_health:
            # Machine has reached its failure state, schedule failure event. 
            self.env.schedule_event(self.env.now, self, self.fail, source)
        elif self.health == self.cbm_threshold:
            # Machine has reached its maintenance threshold and requests maintenance. 
            self.env.schedule_event(self.env.now, self, self.enter_queue, source)
            self.env.schedule_event(
                self.env.now+time_to_degrade, self, self.degrade, source
            )
        else:
            self.env.schedule_event(
                self.env.now+time_to_degrade, self, self.degrade, source
            )

    def enter_queue(self):
        """
        Generate a request for maintenance by entering the maintenance queue.
        """
        if not self.in_queue:
            if self.env.collect_data:
                self.maintenance_data['time'].append(self.env.now)
                self.maintenance_data['event'].append('enter queue')

            self.time_entered_queue = self.env.now
            self.in_queue = True

        if not self.failed and self.maintainer.is_available():
            # Schedule an inspection event if maintainer capacity is available. 
            source = f'{self.name}.enter_queue at {self.env.now}'
            self.env.schedule_event(
                self.env.now, self.maintainer, self.maintainer.inspect, source
            )

    def fail(self):
        """
        Machine failure event. 
        """
        self.failed = True
        self.has_part = False
        self.downtime_start = self.env.now

        if not self.in_queue:
            self.enter_queue()

        if self.env.collect_data:
            self.maintenance_data['time'].append(self.env.now)
            self.maintenance_data['event'].append('failure')

        self.cancel_all_events()

        if self.maintainer.is_available():
            source = f'{self.name}.fail at {self.env.now}'
            self.env.schedule_event(
                self.env.now, self.maintainer, self.maintainer.inspect, source
            )

    def get_cycle_time(self):
        """
        Sample the cycle time of the machine. Should return an integer. 
        """
        return self.cycle_time.sample() 

    def get_time_to_degrade(self):
        """
        Sample a time until the next degradation event according to the specified 
        degradation transition matrix. Should return an integer. 
        """
        if 1 in self.degradation_matrix[self.health]:
            # Machine has no probability of degrading in its current state. 
            return float('inf')

        ttd = 0
        next_health = self.health
        while next_health == self.health:
            ttd += 1
            next_health = random.choices(
                population=range(self.failed_health+1),
                weights=self.degradation_matrix[self.health],
                k=1
            )[0]
        return ttd
    
    def maintain(self):
        """
        Conduct a repair on the machine.
        """
        if not self.failed:
            self.downtime_start = self.env.now
        self.has_part = False
        self.has_finished_part = False
        self.under_repair = True

        if self.env.collect_data:
            self.maintenance_data['time'].append(self.env.now)
            self.maintenance_data['event'].append('begin maintenance')
        
        self.in_queue = False 
        time_to_repair = self.get_time_to_repair()
        
        # Cancel all pending simulation events on this machine. 
        self.cancel_all_events()
        
        # Schedule a future restoration event on this machine.
        source = f'{self.name}.maintain at {self.env.now}'
        self.env.schedule_event(self.env.now+time_to_repair, self, self.restore, source)

    def maintain_planned_failure(self):
        self.failed = True
        self.downtime_start = self.env.now
        self.under_repair = True

        if self.env.collect_data:
            self.maintenance_data['time'].append(self.env.now)
            self.maintenance_data['event'].append('planned failure')
        
        self.cancel_all_events()
        
        time_to_repair = self.planned_failure[1]
        source = f'{self.name}.maintain_planned_failure at {self.env.now}'
        self.env.schedule_event(
            self.env.now+time_to_repair, self, self.restore, source
        )

    def restore(self):
        """
        Restore a machine to perfect health after undergoing maintenance.
        """
        self.health = 0
        self.under_repair = False
        self.failed = False
        
        self.maintainer.utilization -= 1

        self.downtime += (self.env.now - self.downtime_start)

        if self.env.collect_data:
            self.maintenance_data['time'].append(self.env.now)
            self.maintenance_data['event'].append('repaired')

            self.health_data['time'].append(self.env.now)
            self.health_data['health'].append(self.health)  

        source = f'{self.name}.restore at {self.env.now}'
        self.env.schedule_event(self.env.now, self, self.request_part, source)
        time_to_degrade = self.get_time_to_degrade()
        self.env.schedule_event(
            self.env.now+time_to_degrade, self, self.degrade, source
        )
        
        # Schedule a maintainer inspection event once released from this job.
        self.env.schedule_event(
            self.env.now, self.maintainer, self.maintainer.inspect, source
        )

        self.repair_addon_process()

    def repair_addon_process(self):
        """
        Called once the machine is restored after maintenance. 
        """
        pass
    
    def requesting_maintenance(self):
        return (
            (not self.under_repair)
            and ((self.failed) or (self.health >= self.cbm_threshold))
            and (not self.assigned_maintenance)
        )
        
    def get_time_to_repair(self):
        if self.failed:
            return self.cm_distribution.sample()
        else:
            return self.pm_distribution.sample()
        
    def define_routing(self, upstream=[], downstream=[]):
        self.upstream = upstream
        self.downstream = downstream

    def can_receive(self):
        return (
            (not self.under_repair)
            and (not self.failed)
            and (not self.has_part)
        )

    def can_give(self):
        return (
            (self.has_finished_part)
            and (not self.under_repair)
            and (not self.failed)
        ) or (
            (self.has_finished_part)
            and (self.downtime_start == self.env.now)
        )

    def has_content_request(self):
        # Check if a machine has an existing request for a part
        for event in self.env.events:
            if (
                ((event.location is self.name) and (event.action.__name__ == 'request_part'))
                or ((event.location is self.name) and (event.action.__name__ == 'get_part'))
            ):
                return True
        return False

    def has_vacancy_request(self):
        for event in self.env.events:
            if (event.location is self.name) and (event.action.__name__ == 'request_space'):
                return True
        return False

    def cancel_all_events(self):
        """
        Cancel all simulation events scheduled on this machine.
        """
        for event in self.env.events:
            if event.location == self.name:
                event.canceled = True

    def get_candidate_givers(self, blocked=False):
        if blocked:
            # Get only candidate givers that can give a part
            return [obj for obj in self.get_candidate_givers() if obj.blocked]
        else:
            return [obj for obj in self.upstream if obj.can_give()]

    def get_candidate_receivers(self, starved=False):
        if starved:
            return [obj for obj in self.get_candidate_receivers() if obj.starved]
        else:
            # Get only candidate receivers that can accept a part
            return [obj for obj in self.downstream if obj.can_receive()]
