import random

from .machine import Machine
from .part import Part

class Source:
    """
    Introduces unprocessed parts to the system. By default, machines downstream of a 
    source are never starved. 


    Parameters
    ----------
    name : str
        Name of the source. 
    interarrival_time : ``None`` or ``simantha.simulation.Distribution``
        Time between arriving parts. If ``None``, there is no delay between arrivals.
    part_type : ``simantha.Part``
        Class of part objects produced by the source. A part class that inherits 
        ``simantha.Part`` can be used to modify part atrributes and behavior. 


    Methods
    -------
    define_routing(downstream=[])
        Specifies objects downstream of the source. The ``downstream`` argument should 
        be a list of machines that retrieve parts from the source. 


    .. warning:: 
        It is currently assumed that machines downstream of a source object are never 
        starved. Intermittent part arrivals have not been thoroughly tested.

    """
    def __init__(
        self,
        name='Source',
        interarrival_time=None,
        part_type=Part
    ):
        self.name = name
        self.interarrival_time = interarrival_time
        self.last_arrival = 0

        self.part_type = part_type
        
        if self.interarrival_time is None:
            self.level = float('inf')
        else:
            self.level = 0

        self.define_routing()

        self.env = None

    def initialize(self):
        self.reserved_content = 0

        self.part_id = 1

        # Schedule part request for each downstream machine
        for receiver in self.downstream:
            if isinstance(receiver, Machine) and receiver.can_receive():
                receiver.starved = False
                self.env.schedule_event(
                    self.env.now, 
                    receiver, 
                    receiver.request_part,
                    f'{self.name}.arrival at {self.env.now}'
                )
        
    def generate_arrival(self):
        if self.interarrival_time is None:
            return
            
        self.last_arrival += 1
        if (self.last_arrival >= self.interarrival_time) and self.is_empty():
            self.level += 1
            self.last_arrival = 0
            
    def get(self, quantity=1):
        self.reserved_content -= quantity
        
        if not self.is_empty():
            self.level -= quantity
            new_part = self.part_type(id_=self.part_id)
            new_part.initialize()
            self.part_id += 1
            
            return new_part
        else:
            raise RuntimeError('Attempting to take part from source before arrival.')
    
    def reserve_content(self, quantity=1):
        self.reserved_content += quantity

    def is_empty(self):
        return self.level == 0
    
    def define_routing(self, upstream=[], downstream=[]):
        self.upstream = upstream
        self.downstream = downstream

    def can_give(self):
        # TODO: this assumes receivers of this source are never starved
        return True

    def get_candidate_givers(self):
        return self.upstream

    def get_candidate_receivers(self, only_free=False):
        if only_free:
            # Get only candidate receivers that can accept a part
            return [obj for obj in self.get_candidate_receivers() if obj.can_receive()]
        else:
            return [obj for obj in self.downstream if obj.can_receive()]