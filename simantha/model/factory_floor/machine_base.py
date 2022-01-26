from .asset import Asset
from ..simulation import EventType
from ...utils.utils import assert_is_instance


class MachineBase(Asset):
    '''Base class for machine assets in the system.'''

    def __init__(self,
                 name = None,
                 upstream = [],
                 value = 0):
        super().__init__(name, value)

        self._downstream = []
        self._upstream = []  # Needed for the setter to work
        self.upstream = upstream

        self._part = None
        self._waiting_for_space_availability = False
        self._env = None

    @property
    def is_operational(self):
        return True

    @property
    def upstream(self):
        return self._upstream

    @upstream.setter
    def upstream(self, upstream):
        assert_is_instance(upstream, list)
        for up in self._upstream:
            up._remove_downstream(self)

        self._upstream = upstream
        for up in self._upstream:
            assert_is_instance(up, MachineBase)
            up._add_downstream(self)

    def _add_downstream(self, downstream):
        self._downstream.append(downstream)

    def _remove_downstream(self, downstream):
        self._downstream.remove(downstream)

    def _schedule_pass_part_downstream(self):
        self._waiting_for_space_availability = False
        self._env.schedule_event(self._env.now, self.id, self._pass_part_downstream,
                                 EventType.PASS_PART, f'From {self.name}')

    def _pass_part_downstream(self):
        if not self.is_operational or self._part == None: return

        for dwn in self._downstream:
            if dwn._give_part(self._part):
                self._part = None
                self._notify_upstream_of_available_space()
                return
        # Could not pass part downstream
        self._waiting_for_space_availability = True

    def _notify_upstream_of_available_space(self):
        for up in self._upstream:
            up._space_available_downstream()

    def _space_available_downstream(self):
        if self.is_operational and self._waiting_for_space_availability:
            self._schedule_pass_part_downstream()

    def _give_part(self, part):
        ''' Returns True if part has been accepted, otherwise False.
        '''
        assert part != None, 'Cannot give part=None.'
        if not self.is_operational or self._part != None:
            return False

        self._part = part
        self._part.routing_history.append(self.name)
        self._on_received_new_part(self._part)
        return True

    def _on_received_new_part(self, part):
        self._schedule_pass_part_downstream()

