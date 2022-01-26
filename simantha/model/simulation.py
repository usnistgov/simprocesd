import bisect
import json
import random
import sys
import traceback
from enum import IntEnum, unique, auto

from ..utils import assert_is_instance


@unique
class EventType(IntEnum):
    '''Events in the order of highest to lowest priority. Default events are all
    ints. To give a custom priority to an event specify a value that is slightly
    higher or lower than another event. For example,
    event_type = EventType.FAIL + 0.1 -- this type of event will be executed
    with a slightly lower priority than EventType.FAIL'''
    OTHER_HIGH = auto()
    RESTORE = auto()

    # Order of the next 3 events is required for correct machine throughput.
    FINISH_PROCESSING = auto()
    PASS_PART = auto()

    FAIL = auto()
    SENSOR = auto()
    OTHER_LOW = auto()

    TERMINATE = auto()


class Event:
    '''
    Simulation event class. Should be extended when implementing custom simulation
    events.
    '''

    def __init__(self, time, asset_id, action, event_type, message = '', status = ''):
        assert_is_instance(asset_id, int)
        assert_is_instance(time, (float, int))
        assert callable(action), 'Passed in action is not callable.'

        self.time = time
        self.asset_id = asset_id
        self.action = action
        self.event_type = event_type
        self.message = message
        self.status = status

        self.paused_at = None
        self.canceled = False
        self.executed = False

    def execute(self):
        if not self.canceled:
            self.action()
        else:
            self.status = 'canceled'
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


class Environment:
    """
    The main simulation environment for Simantha. This is designed to be an environment
    specifically for use with Simantha objects and is not intended to be a general
    simulation engine. In general, users of Simantha should not need to instantiate an
    Environment object.
    """

    def __init__(self, name = 'environment', trace = False, collect_data = True):
        self.events = []
        self.paused_events = []
        self.name = name
        self.now = 0

        self.terminated = False

        self.trace = trace
        if self.trace:
            self.event_trace = {}

        self.collect_data = collect_data

    def run(self, simulation_time = 0):
        """
        Simulate the system for the specified run time or until no simulation events
        remain.
        """
        self.now = 0
        self.simulation_time = simulation_time
        self.terminated = False
        self.events.append(Event(simulation_time, -1, self.terminate, EventType.TERMINATE))
        self.event_index = 0

        self.events.sort()

        while self.events and not self.terminated:
            self.step()
            self.event_index += 1

        self.export_trace()

    def step(self):
        """
        Find and execute the next earliest simulation event. Simultaneous events are
        executed in order according to their event type priority, then their
        user-assigned priority. If these values are equal then ties are broken randomly.
        """
        next_event = self.events.pop(0)

        self.now = next_event.time

        try:
            if self.trace:
                self.trace_event(next_event)
            next_event.execute()
        except Exception:
            self.export_trace()
            print('Failed event:')
            print(f'  time:     {next_event.time}')
            print(f'  asset_id: {next_event.asset_id}')
            print(f'  action:   {next_event.action.__name__}')
            print(f'  event_type: {next_event.event_type.name}')
            print(f'  message: {next_event.message}')
            print(f'  status: {next_event.status}')
            print(traceback.format_exc())
            sys.exit()

    def schedule_event(self, time, asset_id, action, event_type = EventType.OTHER_LOW,
                       message = ''):
        """
        Schedule a new simulation event by inserting it in its proper asset_id
        within the simulation events list.
        """
        assert time >= self.now, \
            f'Can not schedule events in the past: now={self.now}, time={time}'
        new_event = Event(time, asset_id, action, event_type, message)
        bisect.insort(self.events, new_event)

    def terminate(self):
        self.terminated = True

    def trace_event(self, event):
        if self.trace:
            self.event_trace[self.event_index] = {'time': self.now,
                                                  'asset_id': event.asset_id,
                                                  'action': event.action.__name__,
                                                  'message': event.message,
                                                  'event_type': event.event_type,
                                                  'status': event.status}

    def export_trace(self):
        if self.trace:
            with open(f'{self.name}_trace.json', 'w') as fp:
                json.dump(self.event_trace, fp)

    def cancel_matching_events(self, asset_id = None, action = None):
        if asset_id == None and action == None: return  # No parameters were set

        events_to_cancel = self.events
        if asset_id != None:
            events_to_cancel = [x for x in events_to_cancel if x.asset_id == asset_id]
        if action != None:
            events_to_cancel = [x for x in events_to_cancel if x.action == action]

        for event in events_to_cancel:
            event.canceled = True

    def pause_matching_events(self, asset_id = None, action = None):
        if asset_id == None and action == None: return  # No parameters were set

        events_to_pause = self.events
        if asset_id != None:
            events_to_pause = [x for x in events_to_pause if x.asset_id == asset_id]
        if action != None:
            events_to_pause = [x for x in events_to_pause if x.action == action]

        for event in events_to_pause:
            self.paused_events.append(event)
            self.events.remove(event)
            event.paused_at = self.now

    def unpause_matching_events(self, asset_id = None, action = None):
        if asset_id == None and action == None: return  # No parameters were set

        events_to_unpause = self.paused_events
        if asset_id != None:
            events_to_unpause = [x for x in events_to_unpause if x.asset_id == asset_id]
        if action != None:
            events_to_unpause = [x for x in events_to_unpause if x.action == action]

        for event in events_to_unpause:
            self.paused_events.remove(event)
            event.time += self.now - event.paused_at
            bisect.insort(self.events, event)


class Distribution:
    """
    A class for representing random probability distributions. Should return an integer
    value when sampled.


    Parameters
    ----------
    distribution : int or dict
        If an ``int`` is passed, the distribution will return a constant value when
        sampled. Otherwise, the built-in distributions are discrete uniform, specified
        by passing ``{'uniform': [a, b]}`` to the distribution object, and geometric,
        specified via ``{'geometric': p}``.


    Methods
    -------
    sample()
        Returns a single integer value from the specified distribution. This method
        should be overridden by children of the ``Distribution`` class.

    """

    def __init__(self, distribution):
        if type(distribution) == int:
            self.distribution_type = 'constant'
            self.distribution_parameters = distribution
        elif type(distribution) != dict:
            raise ValueError(
        f'Invalid distribution {distribution}. Distribution should be a dictionary'
        )
        elif len(distribution) > 1:
            raise ValueError(
        f'Invalid distribution {distribution}. Too many dictionary members'
        )
        else:
            for distribution_type, distribution_parameters in distribution.items():
                self.distribution_type = distribution_type
                self.distribution_parameters = distribution_parameters

        if self.distribution_type == 'constant':
            self.mean = self.distribution_parameters
        elif self.distribution_type == 'uniform':
            self.mean = sum(self.distribution_parameters) / 2
        elif self.distribution_type == 'geometric':
            self.mean = 1 / self.distribution_parameters
        else:
            self.mean = None

    def sample(self):
        if self.distribution_type == 'constant':
            return self.distribution_parameters

        elif self.distribution_type == 'uniform':
            a, b = self.distribution_parameters
            return random.randint(a, b)

        elif self.distribution_type == 'geometric':
            # Returns the number of trials needed to achieve a single success, where the
            # probability of success for each trial is p.
            p = self.distribution_parameters
            s = 1
            while random.random() > p:
                s += 1
            return s
