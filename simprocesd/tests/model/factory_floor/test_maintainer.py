from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, EventType, System
from ....model.factory_floor import Machine, Maintainer


class MaintainerTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 2
        self.machines = []
        for i in range(3):
            self.machines.append(MagicMock(spec = Machine))
            self.machines[i].name = f'machine_{i}'
            # Configure the capacity to fix and time to fix.
            self.machines[i].get_work_order_capacity.return_value = i + 1
            self.machines[i].get_work_order_duration.return_value = 10 * (i + 1)
            self.machines[i].get_work_order_cost.return_value = 100 * (i + 1)

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

    def test_request_lifecycle(self):
        mt = Maintainer(capacity = 5)
        mt.initialize(self.env)

        self.machines[0].get_work_order_capacity.assert_not_called()
        tag = object()  # Tag should support any object type.
        order_info = 'test'
        self.assertTrue(mt.create_work_order(self.machines[0], tag, order_info))
        self.assertEqual(mt.total_capacity, 5)
        self.assertEqual(mt.available_capacity, 5 - 1)
        self.assert_last_scheduled_event(self.env.now, mt.id, None, EventType.START_WORK)
        self.machines[0].get_work_order_capacity.assert_called_once_with(tag)
        self.env.add_datapoint.assert_called_once_with(
            'enter_queue', mt.name, (self.env.now, self.machines[0].name, tag, order_info))

        self.machines[0].get_work_order_duration.assert_not_called()
        self.machines[0].start_work.assert_not_called()
        self.machines[0].get_work_order_cost.assert_not_called()
        self.assertEqual(mt.value, 0)
        # Execute beginning of the work order.
        self.env.schedule_event.call_args[0][2]()
        self.assertEqual(mt.available_capacity, 5 - 1)
        self.assert_last_scheduled_event(self.env.now + 10, mt.id, None, EventType.FINISH_WORK)
        self.machines[0].get_work_order_duration.assert_called_once_with(tag)
        self.machines[0].start_work.assert_called_once_with(tag)
        self.machines[0].get_work_order_cost.assert_called_once_with(tag)
        self.assertEqual(mt.value, -100)
        self.env.add_datapoint.assert_called_with(
            'start_work_order', mt.name, (self.env.now, self.machines[0].name, tag, order_info))

        self.machines[0].end_work.assert_not_called()
        # Execute end of the work order.
        self.env.schedule_event.call_args[0][2]()
        self.assertEqual(mt.available_capacity, 5)
        self.machines[0].end_work.assert_called_once_with(tag)
        self.env.add_datapoint.assert_called_with(
            'finish_work_order', mt.name, (self.env.now, self.machines[0].name, tag, order_info))

    def test_max_capacity(self):
        mt = Maintainer(capacity = 5)
        mt.initialize(self.env)
        self.assertEqual(len(self.env.schedule_event.call_args_list), 0)
        # First request.
        self.assertTrue(mt.create_work_order(self.machines[0]))
        self.assertEqual(mt.available_capacity, 5 - 1)
        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        # Second request.
        self.assertTrue(mt.create_work_order(self.machines[1]))
        self.assertEqual(mt.available_capacity, 5 - 1 - 2)
        self.assertEqual(len(self.env.schedule_event.call_args_list), 2)
        # Third request will be accepted but will not be worked because
        # there is not enough capacity left.
        self.assertTrue(mt.create_work_order(self.machines[2]))
        self.assertEqual(mt.available_capacity, 5 - 1 - 2)
        self.assertEqual(len(self.env.schedule_event.call_args_list), 2)

    def test_requests_acceptance(self):
        mt = Maintainer()
        mt.initialize(self.env)
        self.assertTrue(mt.create_work_order(self.machines[0], 'tag1'))
        self.assertFalse(mt.create_work_order(self.machines[0], 'tag1'))
        self.assertTrue(mt.create_work_order(self.machines[0], 'tag2'))
        self.assertTrue(mt.create_work_order(self.machines[1], 'tag1'))

    def test_work_multiple_pending_requests(self):
        mt = Maintainer(capacity = 1)
        mt.initialize(self.env)
        # Add requests.
        for m in self.machines:
            m.get_work_order_capacity.return_value = 1
            self.assertTrue(mt.create_work_order(m))
        # Make sure only one of the requests was scheduled to be worked.
        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        # Execute events until no new event is scheduled, this will
        # finish processing all requests.
        last_action = None
        while last_action != self.env.schedule_event.call_args[0][2]:
            last_action = self.env.schedule_event.call_args[0][2]
            last_action()
        for m in self.machines:
            m.end_work.assert_called_once()

    def test_avoid_simultaneous_work_on_same_target(self):
        mt = Maintainer(capacity = 999)
        mt.initialize(self.env)

        machine = self.machines[0]
        for x in range(5):
            self.assertTrue(mt.create_work_order(machine, f'tag{x}'))

        self.assertEqual(1, len(mt._active_requests))
        self.assertEqual(4, len(mt._request_queue))
        # Execute events until no new even is scheduled.
        last_action = None
        while last_action != self.env.schedule_event.call_args[0][2]:
            last_action = self.env.schedule_event.call_args[0][2]
            last_action()
            # There should never be more than one work order being
            # performed on the same target.
            self.assertTrue(len(mt._active_requests) <= 1)


if __name__ == '__main__':
    unittest.main()
