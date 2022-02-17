import bisect
from enum import IntEnum, unique, auto
import json
import random
import sys
import traceback

from ..utils import DataStorageType, assert_is_instance, assert_callable


@unique
class EventType(IntEnum):
    ''' Events in the order of highest to lowest priority. Default
    events are all ints. To give a custom priority to an event specify
    a value that is slightly higher or lower than another event.
    For example:
    event_type = EventType.FAIL + 0.1 -- this type of event will be
    executed with a slightly lower priority than EventType.FAIL
    '''
    OTHER_HIGH = auto()
    RESTORE = auto()

    # Order of the next 2 events is required for correct machine throughput.
    FINISH_PROCESSING = auto()
    PASS_PART = auto()

    FAIL = auto()
    SENSOR = auto()
    OTHER_LOW = auto()

    TERMINATE = auto()


class Event:
    ''' Simulation event class. Works together with the Environment class.
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

        self.paused_at = None
        self.cancelled = False
        self.executed = False

    def execute(self):
        if self.cancelled:
            self.status = 'cancelled'
            return
        if not self.executed:
            self.action()
            self.executed = True

    def __lt__(self, other):
        return (
            self.time,
            self.event_type,
            self.asset_id  # IDs are unique and can be used as a tie-breaker.
        ) < (
            other.time,
            other.event_type,
            other.asset_id
        )

    def __str__(self):
        return f'Event: time={self.time} asset_id={self.asset_id} action={self.action} ' \
        +f'event_type={self.event_type} message={self.message} status={self.status} ' \
        +f'paused_at={self.paused_at} cancelled={self.cancelled} executed={self.executed} '


class Environment:
    '''
    The main simulation environment for Simantha. This is designed to be an environment
    specifically for use with Simantha objects and is not intended to be a general
    simulation engine. In general, users of Simantha should not need to instantiate an
    Environment object.
    '''

    def __init__(self, name = 'environment', trace = False,
                 simulation_data_storage_type = DataStorageType.NONE):
        self.name = name
        self._trace = trace
        self._simulation_data_storage_type = simulation_data_storage_type
        if self._simulation_data_storage_type == DataStorageType.FILE:
            raise NotImplementedError('Storing to file/disk is not supported yet.')

        self.now = 0
        self.simulation_data = {}
        self._events = []
        self._paused_events = []
        self._event_trace = {}
        self._terminated = False
        self._event_index = 0

    def run(self, simulation_time):
        ''' Simulate the system for the specified run time.
        '''
        self.now = 0
        self._event_index = 0
        self._terminated = False
        self.schedule_event(simulation_time, -1, self._terminate, EventType.TERMINATE)

        try:
            while self._events and not self._terminated:
                self.step()
        finally:
            if self._trace:
                self._export_trace()

    def step(self):
        ''' Find and execute the next earliest simulation event.
        Simultaneous _events are executed in order according to their
        event type priority, then their user-assigned priority. If these
        values are equal then ties are broken randomly.
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

    def schedule_event(self, time, asset_id, action, event_type = EventType.OTHER_LOW,
                       message = ''):
        '''
        Schedule a new simulation event by inserting it in its proper asset_id
        within the simulation _events list.
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
        with open(f'{self.name}_trace.json', 'w') as fp:
            json.dump(self._event_trace, fp)

    def cancel_matching_events(self, asset_id = None):
        ''' Finds scheduled events with matching parameters and marks
        then as cancelled.
        '''
        if asset_id == None: return
        events_to_cancel = [x for x in self._events if x.asset_id == asset_id]

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

    def add_datapoint(self, list_label, asset_name, data_point):
        ''' Record a new datapoint/item in the appropriate list. Data
        storage is decided by simulation_data_storage_type parameter
        that was provided to Environment.

        Arguments:
        label -- usually a string indicating the theme of stored data
        in the related list.
        asset_name -- second identified for the list where data_point
        will be added. It indicates which asset the data is related to.
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
                table_dictionary[asset_name].append(data_point)
            except KeyError:
                table_dictionary[asset_name] = [data_point]
        elif self._simulation_data_storage_type == DataStorageType.FILE:
            raise NotImplementedError('Storing to file/disk is not supported yet.')
