import bisect
from enum import IntEnum, unique, auto
import json
import os
import random

from ..utils import DataStorageType, assert_is_instance, assert_callable


@unique
class EventType(IntEnum):
    '''Events in the order of lowest to highest priority.

    EventType priority makes a difference when multiple events are
    scheduled to happen at the exact same time, in those cases events
    with higher priority are executed first

    To give a custom priority to an event you can specify a value that
    is slightly higher or lower than another event. For example:
    "event_type = EventType.FAIL - 0.1". An event with this event_type
    will be executed with a slightly lower priority than EventType.FAIL
    '''
    TERMINATE = auto()

    OTHER_LOW_PRIORITY = auto()
    START_WORK = auto()
    SENSOR = auto()
    FAIL = auto()

    # Order of the next 2 events is required for correct machine throughput.
    PASS_PART = auto()
    FINISH_PROCESSING = auto()

    RESTORE = auto()
    FINISH_WORK = auto()
    OTHER_HIGH_PRIORITY = auto()


class Event:
    '''Class used for scheduling actions within the simulation.

    | Higher Event priority is determined by:
    | 1. lower <time>
    | 2. if there is a tie, then higher <event_type>
    | 3. if there is a tie, then a lower random weight
    | 4. if there is a tie, then lower <asset_id>

    Arguments
    ---------
    time: float
        Simulation time when the event will be executed.
    asset_id: int
        ID of the Asset who the action belongs to.
    action: function
        Action to be executed, a function with no arguments.
    event_type: float
        Priority of the event, recommended to use EventType enum.
    message: str, default=''
        Any message to be associated with this Event. Useful as
        debugging information.
    '''

    def __init__(self, time, asset_id, action, event_type, message = ''):
        assert_is_instance(asset_id, int)
        assert_is_instance(time, (float, int))
        assert_callable(action, False)

        self.time = time
        self.asset_id = asset_id
        self.action = action
        self.event_type = event_type
        self.message = message
        self.status = ''
        self.random_weight = random.random()

        self.paused_at = None
        self.cancelled = False
        self.executed = False

    def execute(self):
        '''Calls the event's action unless the event is marked as
        cancelled or as executed.
        '''
        if self.cancelled:
            self.status = 'cancelled'
            return
        if not self.executed:
            self.action()
            self.executed = True

    def __lt__(self, other):
        return (
            self.time,
            -self.event_type,
            self.random_weight,
            # A reliable tie-breaker because asset IDs are unique
            self.asset_id
        ) < (
            other.time,
            -other.event_type,
            other.random_weight,
            other.asset_id
        )

    def __str__(self):
        return f'Event: time={self.time} asset_id={self.asset_id} action={self.action} ' \
        +f'event_type={self.event_type} message={self.message} status={self.status} ' \
        +f'paused_at={self.paused_at} cancelled={self.cancelled} executed={self.executed} '


class Environment:
    ''' Simulation environment.

    Responsible for creating, prioritizing, executing, and otherwise
    managing Events.

    Note
    ----
    Environment is automatically created by System and generally should
    not be created manually.

    Arguments
    ---------
    name: str, default='environment'
        Environment name.
    simulation_data_storage_type: DataStorageType, default=DataStorageType.NONE
        How to store <simulation_data>. Does not currently support
        DataStorageType.FILE

    Attributes
    ----------
    now: float
        Current time of the simulation, starts at 0.
    simulation_data: list
        Stored datapoints added with Environment.add_datapoint
    '''

    def __init__(self, name = 'environment', simulation_data_storage_type = DataStorageType.NONE):
        self.name = name
        self._simulation_data_storage_type = simulation_data_storage_type
        if self._simulation_data_storage_type == DataStorageType.FILE:
            raise NotImplementedError('Storing to file/disk is not supported yet.')
        self.reset()

    def reset(self):
        '''Reset the Environment to its initial state.

        This will clear out all scheduled and paused events and reset
        the simulation_data table. To preserve the old data save a
        reference to simulation_data before calling reset, the reference
        can then be used to access old data.
        '''
        self.now = 0
        self.simulation_data = {}
        self._events = []
        self._paused_events = []
        self._terminated = False
        self._event_trace = {}
        self._trace = False
        self._event_index = 0

    def run(self, simulation_duration, trace = False):
        '''Simulate the system for a limited duration.

        Will repeatedly execute a scheduled Event with the highest
        priority until specified simulation time passes.

        Arguments
        ---------
        simulation_duration: float
            For how long to run the simulation. Measured in simulation
            time.
        trace: bool, default=False
            If True then executed Events will be recorded and exported
            to a file at: '~/Downloads/{environment.name}_trace.json'
        '''
        self._trace = trace

        self.schedule_event(self.now + simulation_duration, -1, self._terminate, EventType.TERMINATE)

        try:
            while self._events and not self._terminated:
                self.step()
            self._terminated = False
        finally:
            if self._trace:
                self._export_trace()

    def step(self):
        '''Execute a scheduled Event with the highest priority.
        '''
        next_event = self._events.pop(0)

        self.now = next_event.time

        try:
            if self._trace:
                self._trace_event(next_event)
            next_event.execute()
        except Exception as e:
            print('Failed event:')
            print(f'  time:     {next_event.time}')
            print(f'  asset_id: {next_event.asset_id}')
            print(f'  action:   {next_event.action.__name__}')
            print(f'  event_type: {next_event.event_type}')
            print(f'  message: {next_event.message}')
            print(f'  status: {next_event.status}')
            raise e

    def schedule_event(self, time, asset_id, action, event_type = EventType.OTHER_LOW_PRIORITY,
                       message = ''):
        '''Schedule an Event to be executed at a later simulation time.

        Arguments
        ---------
        time: float
            Simulation time of when to perform the action. Cannot be
            lower than the current simulation time (Environment.now).
        asset_id: int
            ID of the actor Asset. Should follow the rule that if the
            actor Asset were to shutdown then this event should be
            paused/cancelled.
        action: function
            Action to be executed, a function with no arguments.
        event_type: float, default=EventType.OTHER_LOW_PRIORITY
            Priority of the event, recommended to use EventType enum.
        message: str, default=''
            Any message to be associated with this Event. Useful as
            debugging information.
        '''
        if time < self.now:
            raise ValueError(f'Can not schedule _events in the past: now={self.now}, time={time}')
        new_event = Event(time, asset_id, action, event_type, message)
        bisect.insort(self._events, new_event)

    def _terminate(self):
        self._terminated = True

    def _trace_event(self, event):
        self._event_trace[self._event_index] = {'time': self.now,
                                                'asset_id': event.asset_id,
                                                'action': event.action.__name__,
                                                'message': event.message,
                                                'event_type': event.event_type,
                                                'status': event.status}
        self._event_index += 1

    def _export_trace(self):
        with open(os.path.expanduser(f'~/Downloads/{self.name}_trace.json'), 'w') as fp:
            json.dump(self._event_trace, fp)

    def cancel_matching_events(self, asset_id = None):
        '''Find scheduled Events with matching parameters and mark them
        as cancelled.

        Arguments
        ---------
        asset_id: int, optional
            If set, will only match events with the same asset_id
        '''
        if asset_id == None: return
        # Cancel events that are scheduled and ones that are paused.
        events_to_cancel = [x for x in self._events + self._paused_events if x.asset_id == asset_id]

        for event in events_to_cancel:
            event.cancelled = True

    def pause_matching_events(self, asset_id = None):
        '''Find scheduled Events with matching parameters and mark them
        as Paused. Paused Events can be resumed with
        environment.unpause_matching_events

        Arguments
        ---------
        asset_id: int, optional
            If set, will only match events with the same asset_id
        '''
        if asset_id == None: return
        events_to_pause = [x for x in self._events if x.asset_id == asset_id]

        for event in events_to_pause:
            self._paused_events.append(event)
            self._events.remove(event)
            event.paused_at = self.now

    def unpause_matching_events(self, asset_id = None):
        '''Find paused Events with matching parameters and unpause them.

        The Events to be unpaused will be scheduled for their original
        time plus the duration of their pause.

        Arguments
        ---------
        asset_id: int, optional
            If set, will only match events with the same asset_id
        '''
        if asset_id == None: return
        events_to_unpause = [x for x in self._paused_events if x.asset_id == asset_id]

        for event in events_to_unpause:
            self._paused_events.remove(event)
            event.time += self.now - event.paused_at
            bisect.insort(self._events, event)

    def add_datapoint(self, list_label, sub_label, datapoint):
        '''Record a new datapoint/item in the appropriate list.

        Calling env.simulation_data[list_label][sub_label] will return
        a list of all datapoint that were created using the same labels.

        Arguments
        ---------
        label: object
            Primary label. Usually a string describing the datapoint.
        sub_label: object
            Secondary label. Usually a string specifying the source of
            data like an Asset name.
        datapoint: object
            New datapoint that will be added to the list using
            list.append(datapoint). Can be a single object or a tuple.
        '''
        if self._simulation_data_storage_type == DataStorageType.NONE:
            return
        elif self._simulation_data_storage_type == DataStorageType.MEMORY:
            try:
                table_dictionary = self.simulation_data[list_label]
            except KeyError:
                # Using KeyError to indicate dictionary entry needs
                # initialization for better overall performance.
                table_dictionary = {}
                self.simulation_data[list_label] = table_dictionary

            try:
                table_dictionary[sub_label].append(datapoint)
            except KeyError:
                table_dictionary[sub_label] = [datapoint]
        elif self._simulation_data_storage_type == DataStorageType.FILE:
            raise NotImplementedError('Storing to file/disk is not supported yet.')
