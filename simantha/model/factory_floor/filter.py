from .machine_base import MachineBase


class Filter(MachineBase):
    ''' Allows to filter which parts can be passed between when upstream
    and downstream of this filter.
    Filter does not hold/buffer any parts.

    Arguments:
    should_pass_part -- a callable with signature func(part) that
        returns True if the part is allowed to be passed downstream or
        False if the it is not allowed.
    name -- name of the Filter.
    upstream -- list of upstream machines.
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

