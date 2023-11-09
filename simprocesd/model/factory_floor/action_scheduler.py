from . import Asset
from .. import EventType


class ActionScheduler(Asset):
    '''Performs actions on registered objects based on a schedule.

    An ActionScheduler consists of a number of states with set
    durations. When the current state changes a default or a configured
    action is performed. Many objects can be registered with a single
    ActionScheduler.

    Arguments
    ---------
    schedule: list
        List of the state sequences for this schedule.
        Format: [(duration, state), (duration, state), ...]
            - duration determines how long the state will persist
              before progressing to the next state.
            - state can be any object, it will be provided to the action
              calls as an argument.
    name: str, default=None
        Name of this ActionScheduler.
    is_cyclical: bool, default=True
        If True then the schedule will loop back to first state after
        going through the last state. If False then the last state will
        persist indefinitely once reached.
    '''

    def __init__(self, schedule, name = None, is_cyclical = True):
        assert len(schedule) > 0
        for entry in schedule:
            assert isinstance(entry[0], (int, float))

        super().__init__(name = name)
        self._schedule = schedule.copy()
        self._is_cyclical = is_cyclical

        self._schedule_index = 0
        self._state = None
        self._registered_objects = {}

    def initialize(self, env):
        super().initialize(env)
        self._update_state(False)

    @property
    def current_state(self):
        '''Currently active state.
        '''
        return self._state

    def register_object(self, obj, override_action = None):
        '''Register an object for which to perform scheduled actions.

        When state changes an action will be performed on registered
        objects. Performed action is ActionScheduler.defailt_action or
        override_action if one is provided.

        Trying to register an object that was already
        registered with this ActionScheduler will do nothing.

        Arguments
        ---------
        obj: object
            Object to register with this ActionScheduler. Same object
            can be used later to unregister_object
        override_action: function, default=None
            If provided this action will be performed instead of the
            ActionScheduler.default_action when state changes.
            Function signature is same as default_action:
            override_action(action_scheduler, obj, time, new_state)
            - action_scheduler: this ActionScheduler.
            - obj: registered object.
            - time: current simulation time.
            - new_state: new state of ActionScheduler.

        Returns
        -------
        bool
            True if the object was registered, otherwise False.
        '''
        if not (obj in self._registered_objects):
            self._registered_objects[obj] = override_action
            return True
        else:
            return False

    def unregister_object(self, obj):
        '''Unregister an object from ActionScheduler so actions are no
        longer performed for it.

        Does nothing if the object was not already registered with this
        ActionScheduler.

        Arguments
        ---------
        obj: object
            Object to unregister from this ActionScheduler. Need to be
            one of the object that was registered earlier.the same object
            can be used later to unregister_object

        Returns
        -------
        bool
            True if the object was unregistered, otherwise False.
        '''
        try:
            del self._registered_objects[obj]
            return True
        except KeyError:
            return False

    def _update_state(self, advance_schedule = True):
        if advance_schedule:
            self._schedule_index = self._schedule_index + 1
            if not self._is_cyclical and self._schedule_index >= len(self._schedule):
                return
            self._schedule_index %= len(self._schedule)

        self._state = self._schedule[self._schedule_index][1]
        self._env.add_datapoint('schedule_update', self.name, (self.env.now, self.current_state))
        # Perform default or override actions on registered objects.
        for obj, action in self._registered_objects.items():
            if action == None:
                self.default_action(obj, self.env.now, self.current_state)
            else:
                action(self, obj, self.env.now, self.current_state)
        self._schedule_next_transition(self._schedule[self._schedule_index][0])

    def _schedule_next_transition(self, delay):
        self._env.schedule_event(self._env.now + delay,
                                 self.id,
                                 self._update_state,
                                 EventType.OTHER_HIGH_PRIORITY,
                                 f'Schedule update: {self.name}')

    def default_action(self, obj, time, new_state):
        ''' Default action to be performed for each registered object
        when state changes.

        This action is only performed for objects that were registered
        without an override_action.

        Arguments
        ---------
        obj: object
            Registered object.
        time: float
            Time of the state change which is also the current
            simulation time.
        new_state: object
            New state of ActionScheduler.
        '''
        pass

