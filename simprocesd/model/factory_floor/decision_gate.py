from .part_flow_controller import PartFlowController


class DecisionGate(PartFlowController):
    '''PartFlowController that can conditionally prevent Parts from
    passing between upstream and downstream Devices.

    DecisionGate does not hold/buffer any parts.

    Arguments
    ---------
    should_pass_part: function
        Function receives two arguments: this DecisionGate and the Part
        to be passed. Function should return True if the Part can pass
        and False otherwise.
    name: str, default=None
        Name of the DecisionGate. If name is None then the
        DecisionGate's name will be changed to DecisionGate_<id>
    upstream: list, default=None
        A list of upstream Devices.
    '''

    def __init__(self,
                 should_pass_part,
                 name = None,
                 upstream = None):
        super().__init__(name, upstream)
        self._should_pass_part = should_pass_part

    def give_part(self, part):
        if not self._should_pass_part(self, part):
            return False
        return super().give_part(part)

