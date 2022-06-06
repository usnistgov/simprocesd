from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, EventType, System
from ....model.factory_floor import Machine, Maintainer, MachineStatusTracker


class MaintainerTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 2
        self.machines = []
        for i in range(3):
            self.machines.append(MagicMock(spec = Machine))
            st = MagicMock(spec = MachineStatusTracker)
            self.machines[i].status_tracker = st
            # Configure the capacity to fix and time to fix.
            st.get_time_to_maintain.return_value = 10 * (i + 1)
            st.get_capacity_to_maintain.return_value = i + 1

    def assert_last_scheduled_event(self, time, id_, action, event_type, message = None):
        args, kwargs = self.env.schedule_event.call_args_list[-1]
        self.assertEqual(args[0], time)
        self.assertEqual(args[1], id_)
        if action != None:  # Use None for lambda functions.
            self.assertEqual(args[2], action)
        self.assertEqual(args[3], event_type)
        self.assertIsInstance(args[4], str)
        if message != None:
            self.assertEqual(args[4], message)

    def test_initialize(self):
        mt = Maintainer('m', 7, -20000)
        self.assertIn(mt, self.sys._assets)
        mt.initialize(self.env)
        self.assertEqual(mt.name, 'm')
        self.assertEqual(mt.total_capacity, 7)
        self.assertEqual(mt.available_capacity, 7)
        self.assertEqual(mt.value, -20000)

    def test_re_initialize(self):
        mt = Maintainer('m', 7, -20000)
        mt.initialize(self.env)
        self.assertTrue(mt.request_maintenance(self.machines[0], 'tag'))

        self.assertEqual(mt.available_capacity, 7 - 1)
        mt.initialize(self.env)
        self.assertEqual(mt.available_capacity, 7)
        self.assertEqual(mt._request_queue, [])

    def test_request_lifecycle(self):
        mt = Maintainer(capacity = 5)
        mt.initialize(self.env)

        tag = object()  # Tag should support any object type.
        self.assertTrue(mt.request_maintenance(self.machines[0], tag))
        self.assertEqual(mt.total_capacity, 5)
        # Capacity to fix is configured in setUp.
        self.assertEqual(mt.available_capacity, 5 - 1)
        self.assert_last_scheduled_event(self.env.now, mt.id, None, EventType.OTHER_LOW)
        self.machines[0].status_tracker.get_capacity_to_maintain.assert_called_once_with(tag)
        # Get time should only get called once the maintenance began.
        self.machines[0].status_tracker.get_time_to_maintain.assert_not_called()
        self.machines[0].shutdown.assert_not_called()
        # Execute last scheduled event.
        self.env.schedule_event.call_args[0][2]()
        self.assertEqual(mt.available_capacity, 5 - 1)
        # Time to fix is configured in setUp.
        self.assert_last_scheduled_event(self.env.now + 10, mt.id, None, EventType.RESTORE)
        self.machines[0].status_tracker.get_time_to_maintain.assert_called_once_with(tag)
        self.machines[0].shutdown.assert_called_once()
        self.machines[0].restore_functionality.assert_not_called()
        self.machines[0].status_tracker.maintain.assert_not_called()
        # Execute last scheduled event.
        self.env.schedule_event.call_args[0][2]()
        self.assertEqual(mt.available_capacity, 5)
        self.machines[0].restore_functionality.assert_called_once()
        self.machines[0].status_tracker.maintain.assert_called_once_with(tag)

    def test_max_capacity(self):
        mt = Maintainer(capacity = 5)
        mt.initialize(self.env)
        self.assertEqual(len(self.env.schedule_event.call_args_list), 0)
        # First request.
        self.assertTrue(mt.request_maintenance(self.machines[0]))
        self.assertEqual(mt.available_capacity, 5 - 1)
        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        # Second request.
        self.assertTrue(mt.request_maintenance(self.machines[1]))
        self.assertEqual(mt.available_capacity, 5 - 1 - 2)
        self.assertEqual(len(self.env.schedule_event.call_args_list), 2)
        # Third request will be accepted but will not be worked because
        # there is not enough capacity left.
        self.assertTrue(mt.request_maintenance(self.machines[2]))
        self.assertEqual(mt.available_capacity, 5 - 1 - 2)
        self.assertEqual(len(self.env.schedule_event.call_args_list), 2)

    def test_requests_acceptance(self):
        mt = Maintainer()
        mt.initialize(self.env)
        self.assertTrue(mt.request_maintenance(self.machines[0], 'tag1'))
        self.assertFalse(mt.request_maintenance(self.machines[0], 'tag1'))
        self.assertTrue(mt.request_maintenance(self.machines[0], 'tag2'))
        self.assertTrue(mt.request_maintenance(self.machines[1], 'tag1'))

    def test_work_multiple_pending_requests(self):
        mt = Maintainer(capacity = 1)
        mt.initialize(self.env)
        # Add requests.
        for m in self.machines:
            m.status_tracker.get_capacity_to_maintain.return_value = 1
            self.assertTrue(mt.request_maintenance(m))
        # Make sure only one of the requests was scheduled to be worked.
        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        # Execute next 2 events which will finish processing 1st request.
        last_action = None
        while last_action != self.env.schedule_event.call_args[0][2]:
            last_action = self.env.schedule_event.call_args[0][2]
            last_action()
        for m in self.machines:
            m.status_tracker.maintain.assert_called_once()


if __name__ == '__main__':
    unittest.main()
