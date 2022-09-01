import bisect
from enum import IntEnum, unique, auto
import json
import os
import random

from ..utils import DataStorageType, assert_is_instance, assert_callable


@unique
class EventType(IntEnum):
    ''' Events in the order of lowest to highest priority. EventType
    priority makes a different when multiple events are scheduled to
    happen at the exact same time, in those cases events with higher
    priority are executed first

    To give a custom priority to an event you can specify a value that
    is slightly higher or lower than another event. For example:
    event_type = EventType.FAIL - 0.1
        an event with this event_type will be executed with a slightly
        lower priority than EventType.FAIL, meaning that the FAIL
        event would be executed first if it was scheduled for the
        exact same time.
    '''
    TERMINATE = auto()

    OTHER_LOW_PRIORITY = auto()
    SENSOR = auto()
    FAIL = auto()

    # Order of the next 2 events is required for correct machine throughput.
    PASS_PART = auto()
    FINISH_PROCESSING = auto()

    RESTORE = auto()
    OTHER_HIGH_PRIORITY = auto()


class Event:
    ''' Simulation event class. Works together with the Environment
    class.

    Arguments:
    time - simulation time when the event will be executed.
    asset_id - ID of the Asset who the action belongs to.
    action - action to be executed, a function with no input
        parameters.
    event_type - type of the event, EventType or another numerical
        value.
    message - an accompanying message to be stored in the event logs.
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
        ''' Calls the event's action unless the event is marked as
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
    '''
    The main simulation environment for Sim-PROCESD. By default,
    Environment objects are instantiated automatically by the System.
    '''

    def __init__(self, name = 'environment', simulation_data_storage_type = DataStorageType.NONE):
        self.name = name
        self._simulation_data_storage_type = simulation_data_storage_type
        if self._simulation_data_storage_type == DataStorageType.FILE:
            raise NotImplementedError('Storing to file/disk is not supported yet.')
        self.reset()

    def reset(self):
        ''' Reset the Environment to its initial state. This will clear
        out all scheduled and paused events and make a new
        simulation_data table.
        Reference to the previous simulation_data table can be saved
        before calling reset to preserve the data.
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
        ''' Simulate the system for a limited duration.

        Arguments:
        simulation_duration -- for how long to run the simulation
            measured in simulation time.
        trace -- if True then events will be recorded and exported to
            a file. Otherwise (default) trace is not recorded.
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
        ''' Find and execute the next earliest simulation event.
        Simultaneous _events are executed in order according to Event's
        default comparator.
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
            print(f'  event_type: {next_event.event_type.name}')
            print(f'  message: {next_event.message}')
            print(f'  status: {next_event.status}')
            raise e

    def schedule_event(self, time, asset_id, action, event_type = EventType.OTHER_LOW_PRIORITY,
                       message = ''):
        '''
        Schedule a new simulation event to be executed.

        Arguments:
        time -- when to perform the action. Time cannot be lower than
            the current simulation time (Environment.now).
        asset_id -- id of the actor of the action. If this actor were to
            shutdown then this event should be paused/cancelled.
        action -- this will be called with no additional parameters at
            the specified simulation time.
        event_type -- one of the EventType enum values or a float.
        message -- any message to be associated with this event. Useful
            for debugging information.
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
        ''' Finds scheduled events with matching parameters and marks
        then as cancelled.
        '''
        if asset_id == None: return
        # Cancel events that are scheduled and ones that are paused.
        events_to_cancel = [x for x in self._events + self._paused_events if x.asset_id == asset_id]

        for event in events_to_cancel:
            event.cancelled = True

    def pause_matching_events(self, asset_id = None):
        ''' Finds scheduled events with matching parameters and marks
        then as paused. Paused events can be resumed with
        unpause_matching_events.
        '''
        if asset_id == None: return
        events_to_pause = [x for x in self._events if x.asset_id == asset_id]

        for event in events_to_pause:
            self._paused_events.append(event)
            self._events.remove(event)
            event.paused_at = self.now

    def unpause_matching_events(self, asset_id = None):
        ''' Finds paused events with matching parameters and schedules
        them to be executed at a later time. An unpaused event's
        scheduled time is offset by the duration of its pause.
        '''
        if asset_id == None: return
        events_to_unpause = [x for x in self._paused_events if x.asset_id == asset_id]

        for event in events_to_unpause:
            self._paused_events.remove(event)
            event.time += self.now - event.paused_at
            bisect.insort(self._events, event)

    def add_datapoint(self, list_label, sub_label, data_point):
        ''' Record a new datapoint/item in the appropriate list. Data
        storage is decided by simulation_data_storage_type parameter
        that was provided to Environment.

        Arguments:
        label -- usually a string indicating the theme of stored data
            in the related list.
        sub_label -- second identified for the list where data_point
            will be added. Usually a device name.
        data_point -- new data point that will be added to the list
            using list.append(data_point)
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
                table_dictionary[sub_label].append(data_point)
            except KeyError:
                table_dictionary[sub_label] = [data_point]
        elif self._simulation_data_storage_type == DataStorageType.FILE:
            raise NotImplementedError('Storing to file/disk is not supported yet.')
