from . import Asset
from .. import EventType


class DeviceSchedule(Asset):
    '''Time based schedule used by Devices.

    When DeviceSchedule is not active (see is_active) a Device that
    uses this schedule will not accept new Parts but it will continue
    to process any Parts it already received.

    Arguments
    ---------
    schedule: list
        List of the state sequences for this schedule.
        Format: [(duration, state), (duration, state), ...]
            - state being True means active and False means inactive.
            - duration determines how long the state will persist
            before progressing to the next state.
    name: str, default=None
        Name of this DeviceSchedule.
    is_cyclical: bool, default=True
        If True then the schedule will loop back to first state after
        going through the last state. If False then the last state will
        persist indefinitely once reached.
    '''

    def __init__(self, schedule, name = None, is_cyclical = True):
        assert len(schedule) > 0
        for entry in schedule:
            assert isinstance(entry[0], (int, float))
            assert isinstance(entry[1], bool)

        super().__init__(name = name)
        self._schedule = schedule.copy()
        self._is_cyclical = is_cyclical

        self._schedule_index = 0
        self._is_on = True
        self._devices = []

    def initialize(self, env):
        if self._env == None:
            # First time initializing.
            self._initial_devices = self._devices.copy()
        else:
            # Simulation is resetting, restore starting device list.
            self._devices = self._initial_devices.copy()

        super().initialize(env)
        self._schedule_index = 0
        self._update_status(False)

    @property
    def is_active(self):
        '''Current status of the DeviceSchedule.
        '''
        return self._is_on

    def add_device(self, device):
        '''Add a new Device that depends on this DeviceSchedule.

        Devices need to be added to the DeviceSchedule so the schedule
        can 'wake up' those Devices when the schedule becomes active.

        Note
        ----
        A Device automatically calls this function when a
        DeviceSchedule is assigned to a Device.

        Arguments
        ---------
        device: Device
            Device that is using this DeviceSchedule.
            Does nothing if given Device has already been added.
        '''
        if not (device in self._devices):
            self._devices.append(device)

    def remove_device(self, device):
        '''Remove a Device that no longer depends on this
        DeviceSchedule.

        Note
        ----
        A Device automatically calls this function when a
        DeviceSchedule is unassigned from a Device.

        Arguments
        ---------
        device: Device
            Device that is using this DeviceSchedule.
            Does nothing if given Device has not been previously added.
        '''
        try:
            self._devices.remove(device)
        except ValueError:
            pass

    def _update_status(self, advance_schedule = True):
        if advance_schedule:
            self._schedule_index = self._schedule_index + 1
            if not self._is_cyclical and self._schedule_index >= len(self._schedule):
                return
            self._schedule_index %= len(self._schedule)

        self._is_on = self._schedule[self._schedule_index][1]
        if self.is_active:
            for d in self._devices:
                d.notify_upstream_of_available_space()
        self._env.add_datapoint('schedule_update', self.name, (self.env.now, self.is_active))

        # Status will never change if there are less than 2 entries.
        if len(self._schedule) > 1:
            self._schedule_next_transition(self._schedule[self._schedule_index][0])

    def _schedule_next_transition(self, delay):
        self._env.schedule_event(self._env.now + delay,
                                 self.id,
                                 self._update_status,
                                 EventType.OTHER_HIGH_PRIORITY,
                                 f'Schedule update: {self.name}')

