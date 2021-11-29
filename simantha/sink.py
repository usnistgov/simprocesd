class Sink:
    """Sinks collect finished parts as they exit the system."""
        
    def __init__(self, name='Sink', initial_level=0, collect_parts=False):
        self.name = name
        self.capacity = float('inf')
        self.initial_level = initial_level
        self.level = initial_level
        self.contents = []
        self.collect_parts = collect_parts

        self.env = None

        self.level_data = {'time': [0], 'level': [initial_level]}

    def initialize(self):
        self.level = self.initial_level
        self.contents = []

    def reserve_vacancy(self, quantity=1):
        return

    def put(self, part, quantity=1):
        if self.env.now > self.env.warm_up_time:
            self.level += quantity
            if self.collect_parts:
                self.contents.append(part)

        self.level_data['time'].append(self.env.now)
        self.level_data['level'].append(self.level)

    def define_routing(self, upstream=[], downstream=[]):
        self.upstream = upstream
        self.downstream = downstream

    def can_give(self):
        return False

    def can_receive(self):
        return True
