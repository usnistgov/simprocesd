import random 

from .simulation import *

class Maintainer:
    """
    A maintainer is responsible for repairing machines that request maintenance 
    according to some preventive maintenance policy or upon the occurrence of failure. 


    Parameters
    ----------
    name : str
        Name of the maintainer.
    capacity : int
        The maximum number of machines that the maintainer may repair simultaneously.
    machines : list or ``None``
        A list of machine objects that the maintainer is able to repair. If ``None``, 
        the maintainer may repair any machine in the system.

    
    The following attributes are used to indicate the state of the maintainer.


    Attributes
    ----------
    utilization : int
        The number of machines currently being repaired by the maintainer.


    The following methods may be overridden by extensions of the ``Maintainer`` class.


    Methods
    -------
    choose_maintenance_action(queue)
        Accepts a ``queue`` as a list of machines with unfufilled maintenance requests. 
        Should return a single machine from the queue to repair next. By default, the
        maintainer will choose the machine with the earliest request for maintenance
        (equivalent to a first-in, first-out policy).

    """
    def __init__(self, name='maintainer', capacity=float('inf'), machines=None):
        self.name = name
        self.capacity = capacity

        self.utilization = 0

        self.env = None

        self.machines = machines

    def initialize(self):
        self.utilization = 0

    def is_available(self):
        return self.utilization < self.capacity

    def inspect(self):
        # If available, check for machines requesting repair
        current_queue = self.get_queue()
        if (not self.is_available()) or (len(current_queue) == 0):
            # No available capacity or empty queue
            return
        else:
            machine = self.choose_maintenance_action(current_queue)
            self.utilization += 1
            machine.in_queue = False
            machine.under_repair = True
            source = f'{self.name}.inspect at {self.env.now}'
            self.env.schedule_event(self.env.now, machine, machine.maintain, source)

    def choose_maintenance_action(self, queue):
        """
        Choose a machine to repair from among those in the queue. Uses a first-in, 
        first-out (FIFO) rule by default with ties broken by random selection. This
        method should be overridden by maintainers that implement alternative
        maintenance scheduling rules. 
        """
        earliest_request = min(m.time_entered_queue for m in queue)
        candidates = [m for m in queue if m.time_entered_queue == earliest_request]
        return random.choice(candidates)

    def get_queue(self):
        """
        Get a list of machines currently awaiting maintenance.
        """
        return [machine for machine in self.machines if machine.in_queue]
