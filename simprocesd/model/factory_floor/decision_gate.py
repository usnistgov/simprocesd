from functools import partial

from .part_flow_controller import PartFlowController


class DecisionGate(PartFlowController):
    '''PartFlowController that can conditionally prevent Parts from
    passing between upstream and downstream Devices.

    DecisionGate does not hold/buffer any parts.

    Arguments
    ---------
    name: str, default=None
        Name of the DecisionGate. If name is None then the
        DecisionGate's name will be changed to DecisionGate_<id>
    upstream: list of PartFlowController, default=None
        List of devices from which Parts can be received.
    decider_override: function, default=None
        Function receives two arguments: this DecisionGate and the Part
        to be passed. Function should return True if the Part can pass
        and False otherwise.
        If not None this function will be used instead of
        DecisionGate.part_pass_decider
    '''

    def __init__(self,
                 name = None,
                 upstream = None,
                 decider_override = None):
        super().__init__(name, upstream)
        if decider_override == None:
            self._decider_override = self.part_pass_decider
        else:
            self._decider_override = partial(decider_override, self)

    def give_part(self, part):
        if not self._decider_override(part):
            return False
        return super().give_part(part)

    def part_pass_decider(self, part):
        raise NotImplementedError('DecisionGate does not have a default decider implementations.')

