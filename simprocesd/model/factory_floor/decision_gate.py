from functools import partial

from .part_flow_controller import PartFlowController


class DecisionGate(PartFlowController):
    '''Device that can prevent certain Parts from passing between
    upstream and downstream devices.

    DecisionGate does not hold/buffer any parts.

    Warning
    -------
    DecisionGate should ONLY use the state of the Part being passed
    to determine if the Part should pass. This means the same Part
    will either always pass or never pass unless its state changes.
    If DecisionGate blocks a Part from upstream and later it would
    allow the same Part to pass, there is no guarantee that another
    attempt to pass the Part is going to be made causing the Part to
    get stuck.

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
        '''Decider for whether a Part is allowed to pass through this
        device.

        This decider will not be used if the DecisionGate was provided
        a <decider_override> on creation.

        Warning
        -------
        DecisionGate should ONLY use the state of the Part being passed
        to determine if the Part should pass. This means the same Part
        will either always pass or never pass unless its state changes.
        If DecisionGate blocks a Part from upstream and later it would
        allow the same Part to pass, there is no guarantee that another
        attempt to pass the Part is going to be made causing the Part to
        get stuck.

        Arguments
        ---------
        part: Part
            Part the upstream is trying to pass.

        Returns
        -------
        bool
            Whether the <part> should be allowed to pass.
        '''
        raise NotImplementedError('DecisionGate does not have a default decider implementations.')

