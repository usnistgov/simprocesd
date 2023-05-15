from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ... import mock_wrap
from ....model import Environment, EventType, System
from ....model.factory_floor import Part, Machine, Buffer


class BufferTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 0
        self.upstream = [mock_wrap(Machine()), mock_wrap(Machine())]
        for u in self.upstream:
            u.initialize(self.env)
        self.downstream = MagicMock(spec = Machine)
        self.downstream.give_part.return_value = True

    def assert_last_scheduled_event(self, time, id_, action, event_type, message = None):
        args, kwargs = self.env.schedule_event.call_args_list[-1]
        self.assertEqual(args[0], time)
        self.assertEqual(args[1], id_)
        self.assertEqual(args[2], action)
        self.assertEqual(args[3], event_type)
        self.assertIsInstance(args[4], str)
        if message != None:
            self.assertEqual(args[4], message)

    def test_initialize(self):
        buffer = Buffer('name', self.upstream, 5, 10, 20)
        self.assertIn(buffer, self.sys._assets)
        buffer.initialize(self.env)
        self.assertEqual(buffer.name, 'name')
        self.assertEqual(buffer.upstream, self.upstream)
        self.assertEqual(buffer.value, 20)
        self.assertEqual(buffer.level(), 0)
        self.assertListEqual(buffer.stored_parts, [])

    def test_re_initialize(self):
        buffer = Buffer('name', self.upstream, 5, 10, 20)
        buffer.initialize(self.env)

        part = Part()
        buffer.give_part(part)
        buffer.add_cost('', 3)
        self.assertListEqual(buffer.upstream, self.upstream)
        self.assertEqual(buffer.level(), 1)
        self.assertEqual(buffer.value, 20 - 3)
        self.assertListEqual(buffer.stored_parts, [part])

        buffer.initialize(self.env)
        self.assertEqual(buffer.upstream, self.upstream)
        self.assertEqual(buffer.value, 20)
        self.assertEqual(buffer.level(), 0)
        self.assertListEqual(buffer.stored_parts, [])

    def test_give_pass_part(self):
        part = Part()
        buffer = Buffer('name', self.upstream, minimum_delay = 5, capacity = 10)
        buffer.initialize(self.env)
        buffer._add_downstream(self.downstream)

        self.assertEqual(buffer.level(), 0)
        self.assertEqual(buffer.waiting_for_part_start_time, 0)

        self.env.now = 3
        self.assertTrue(buffer.give_part(part))
        self.assertEqual(buffer.level(), 1)
        self.assertEqual(buffer.waiting_for_part_start_time, 3)
        self.env.now = 4
        self.assertEqual(buffer.level(), 1)
        self.assertEqual(buffer.waiting_for_part_start_time, 3)
        self.assert_last_scheduled_event(3 + 5, buffer.id, buffer._pass_part_downstream,
                                         EventType.PASS_PART)

        self.env.now = 3 + 5
        buffer._pass_part_downstream()
        self.assertEqual(buffer.waiting_for_part_start_time, 3)
        self.downstream.give_part.assert_called_once_with(part)
        self.assertEqual(buffer.level(), 0)

    def test_give_many_parts(self):
        buffer = Buffer('name', self.upstream, minimum_delay = 1, capacity = 4)
        buffer.initialize(self.env)
        buffer._add_downstream(self.downstream)
        parts = []
        # Attempt to pass more parts buffer than capacity will allow.
        for i in range(6):
            parts.append(Part())
            if len(parts) <= 4:
                self.assertTrue(buffer.give_part(parts[i]))
                self.assertEqual(buffer.level(), i + 1)
            else:
                self.assertFalse(buffer.give_part(parts[i]))
                self.assertEqual(buffer.level(), 4)
        for u in self.upstream:
            # Called after receiving first 3 (of 4) parts.
            self.assertEqual(len(u.space_available_downstream.call_args_list), 3)
        self.assertListEqual(buffer.stored_parts, parts[:-2])

        self.env.now += 1
        # One call will attempt to pass all the parts it can.
        buffer._pass_part_downstream()
        self.assertEqual(buffer.level(), 0)
        for u in self.upstream:
            self.assertEqual(len(u.space_available_downstream.call_args_list), 4)
        # Downstream should have been given all 4 parts, the mock was
        # configured to accept all parts.
        self.assertEqual(len(self.downstream.give_part.call_args_list), 4)
        # Verify the order of passed parts.
        for i in range(4):
            args, kwards = self.downstream.give_part.call_args_list[i]
            self.assertEqual(args[0], parts[i])

    def test_minimum_delay(self):
        buffer = Buffer(minimum_delay = 100, capacity = 4)
        buffer.initialize(self.env)
        buffer._add_downstream(self.downstream)
        parts = []
        for i in range(4):
            # Give parts at times: 0, 10, 20, and 30
            parts.append(Part())
            self.assertTrue(buffer.give_part(parts[i]))
            self.env.now += 10
        self.assertEqual(buffer.level(), 4)

        # Try to pass before any Part spent the minimum time.
        self.env.now = 90
        buffer._pass_part_downstream()
        self.assertEqual(buffer.level(), 4)

        # Try to pass when 2 Parts can be passed.
        self.env.now = 110
        buffer._pass_part_downstream()
        self.assertEqual(buffer.level(), 2)
        self.assertEqual(len(self.downstream.give_part.call_args_list), 2)

        # Try to pass when 1 more Part can be passed.
        self.env.now = 120
        buffer._pass_part_downstream()
        self.assertEqual(buffer.level(), 1)
        self.assertEqual(len(self.downstream.give_part.call_args_list), 3)

        # Try to pass when the last Part can be passed.
        self.env.now = 200
        buffer._pass_part_downstream()
        self.assertEqual(buffer.level(), 0)
        self.assertEqual(len(self.downstream.give_part.call_args_list), 4)

    def test_minimum_delay_rounding_error(self):
        # Minimum delay is smaller than the least significant bit of
        # self.env.now so the Part should pass even if the time has not
        # progressed. This avoids an infinite loop of trying to pass a
        # part, being unable to, and scheduling next pass_part for
        # effectively the same time.
        buffer = Buffer(minimum_delay = 1e-30)
        buffer.initialize(self.env)
        buffer._add_downstream(self.downstream)

        self.env.now = 1000
        part = Part()
        self.assertTrue(buffer.give_part(part))
        buffer._pass_part_downstream()
        self.assertEqual(len(self.downstream.give_part.call_args_list), 1)


if __name__ == '__main__':
    unittest.main()
