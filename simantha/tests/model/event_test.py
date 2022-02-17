import random
from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ...model import Event, EventType


class EventTestCase(TestCase):

    def test_initialize(self):
        action = MagicMock()
        event = Event(1, 1337, action, EventType.TERMINATE, 'test')
        self.assertEqual(event.time, 1)
        self.assertEqual(event.asset_id, 1337)
        self.assertEqual(event.action, action)
        self.assertEqual(event.event_type, EventType.TERMINATE)
        self.assertEqual(event.message, 'test')
        self.assertEqual(event.status, '')
        self.assertEqual(event.paused_at, None)
        self.assertEqual(event.cancelled, False)
        self.assertEqual(event.executed, False)

    def test_execute_action(self):
        action = MagicMock()
        event = Event(1, 1337, action, EventType.TERMINATE)
        self.assertEqual(event.executed, False)
        event.execute()
        self.assertEqual(event.executed, True)

        action.assert_called_once_with()

    def test_execute_called_twice(self):
        action = MagicMock()
        event = Event(1, 1337, action, EventType.TERMINATE)
        event.execute()
        event.execute()
        self.assertEqual(event.executed, True)

        action.assert_called_once()

    def test_execute_cancelled_event(self):
        action = MagicMock()
        event = Event(1, 1337, action, EventType.TERMINATE)
        event.cancelled = True
        event.execute()

        action.assert_not_called()

    def test_event_sorting(self):
        action = MagicMock()
        e1 = Event(1, 1, action, EventType.OTHER_HIGH)
        e2 = Event(2, 1, action, EventType.OTHER_HIGH)
        e3 = Event(1, 1, action, EventType.OTHER_LOW)
        e4 = Event(2, 1, action, EventType.OTHER_LOW)
        e5 = Event(1, 2, action, EventType.OTHER_HIGH)
        e6 = Event(2, 2, action, EventType.OTHER_HIGH)
        e7 = Event(1, 2, action, EventType.OTHER_LOW)
        e8 = Event(2, 2, action, EventType.OTHER_LOW)
        expected = [e1, e5, e3, e7, e2, e6, e4, e8]

        random.seed(1)
        for i in range(10):
            new_list = expected.copy()
            while new_list == expected:  # ensure lists are different
                random.shuffle(new_list)
            new_list = sorted(new_list)
            self.assertListEqual(new_list, expected, f'i = {i}')


if __name__ == '__main__':
    unittest.main()
