import random 

from .simulation import *


class Maintainer:
    """
    A maintainer is responsible for repairing machines that request maintenance 
    according to some preventive maintenance policy or upon the occurrence of failure. 
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
