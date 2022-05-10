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

    def test_less_than(self):
        # Event only defines a less-than operator, __lt__, for sorting.
        action = MagicMock()
        e1 = Event(1, 1, action, EventType.FAIL)
        e1.random_weight = 0.5
        e2 = Event(1, 1, action, EventType.FAIL)
        e2.random_weight = 0.5
        self.assertFalse(e1 < e2 or e2 < e1)

        e1.asset_id = 0
        self.assertLess(e1, e2)

        e2.random_weight = 0
        self.assertLess(e2, e1)

        e1.event_type = EventType.OTHER_HIGH
        self.assertLess(e1, e2)

        e2.time = 0
        self.assertLess(e2, e1)


if __name__ == '__main__':
    unittest.main()
