class Part:
    """
    A part object created by a source to be processed by the system. Stored the name of
    each source, machine, buffer, and sink visited by the part. 
    """
    def __init__(self, id_):
        self.id_ = id_
        self.routing_history = []

    def initialize(self):
        pass
