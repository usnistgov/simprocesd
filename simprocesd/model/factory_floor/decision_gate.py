from .device import Device


class DecisionGate(Device):
    '''Device that can conditionally prevent Parts from passing between
    upstream and downstream Devices.

    DecisionGate does not hold/buffer any parts.

    Arguments
    ---------
    should_pass_part: function
        Function receives one argument: Part to be passed and should
        return True if the Part can pass or False if it cannot.
    name: str, default=None
        Name of the DecisionGate. If name is None then the
        DecisionGate's name will be changed to DecisionGate_<id>
    upstream: list, default=[]
        A list of upstream Devices.
    '''

    def __init__(self,
                 should_pass_part,
                 name = None,
                 upstream = []):
        super().__init__(name, upstream, 0)
        self._should_pass_part = should_pass_part

    def give_part(self, part):
        assert part != None, 'Part cannot be set to None.'
        if not self.is_operational() or not self._should_pass_part(part):
            return False

        for dwn in self._downstream:
            if dwn.give_part(part):
                return True
        return False

    def space_available_downstream(self):
        if self.is_operational():
            self.notify_upstream_of_available_space()

    def _pass_part_downstream(self, part):
        # Safety check, function should never be called.
        raise RuntimeError('This method should never be called.')

