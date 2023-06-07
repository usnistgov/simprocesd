from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ... import mock_wrap
from ....model import Environment, EventType, System
from ....model.factory_floor import Part, Machine, Source


class SourceTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 0

    def assert_last_scheduled_event(self, time, id_, action, event_type, message = None):
        args, kwargs = self.env.schedule_event.call_args_list[-1]
        self.assertEqual(args[0], time)
        self.assertEqual(args[1], id_)
        self.assertEqual(args[2], action)
        self.assertEqual(args[3], event_type)
        self.assertIsInstance(args[4], str)
        if message != None:
            self.assertEqual(args[4], message)

    def test_init(self):
        source = Source('name', Part(), 2, 15)
        self.assertEqual(source.name, 'name')
        self.assertEqual(source.value, 0)
        self.assertEqual(source.upstream, [])
        self.assertEqual(source.produced_parts, 0)
        self.assertEqual(source.cost_of_produced_parts, 0)
        self.assertEqual(source.cycle_time, 2)
        self.assertIn(source, self.sys._assets)

    def test_initialize(self):
        source = Source(cycle_time = 6, sample_part = Part(value = 5))
        source.initialize(self.env)
        self.assert_last_scheduled_event(6, source.id, source._finish_processing_part,
                                         EventType.FINISH_PROCESSING)

        self.env.now = 6
        source._finish_processing_part()
        self.assertEqual(source.value, 0)
        self.assertEqual(source.produced_parts, 0)
        self.assertEqual(source.cost_of_produced_parts, 0)
        self.assert_last_scheduled_event(6, source.id, source._pass_part_downstream,
                                         EventType.PASS_PART)

    def test_re_initialize(self):
        source = Source('name', Part(value = 5), 1, 15)
        downstream = MagicMock(spec = Machine)
        downstream.give_part.return_value = True
        source._add_downstream(downstream)
        source.initialize(self.env)

        source._finish_processing_part()
        source._pass_part_downstream()
        self.assertEqual(source.value, -5)
        self.assertEqual(source.produced_parts, 1)
        self.assertEqual(source.cost_of_produced_parts, 5)
        self.assertEqual(len(self.env.schedule_event.call_args_list), 3)

        source.initialize(self.env)
        self.assertEqual(source.value, 0)
        self.assertEqual(source.produced_parts, 0)
        self.assertEqual(source.cost_of_produced_parts, 0)
        # One new scheduled event due to initialize.
        self.assertEqual(len(self.env.schedule_event.call_args_list), 3 + 1)
        self.assert_last_scheduled_event(1, source.id, source._finish_processing_part,
                                         EventType.FINISH_PROCESSING)

    def test_upstream(self):
        # Source is not allowed to have upstream machines.
        source = Source()

        def helper(): source.set_upstream([Machine()])

        self.assertRaises(ValueError, helper)

    def test_pass_part_downstream(self):
        part = Part('n', 10, 3)
        wrapped_part = mock_wrap(part)
        source = Source(sample_part = wrapped_part, cycle_time = 1)
        downstream = MagicMock(spec = Machine)
        downstream.give_part.return_value = True
        source._add_downstream(downstream)

        source.initialize(self.env)
        wrapped_part.make_copy.assert_not_called()
        self.env.now = 1
        source._finish_processing_part()
        wrapped_part.make_copy.assert_called_once()

        source._pass_part_downstream()
        self.assertEqual(source.value, -10)
        self.assertEqual(source.produced_parts, 1)
        self.assertEqual(source.cost_of_produced_parts, 10)

        args, kwargs = downstream.give_part.call_args
        # arg[0] is the part that was passed with give_part
        self.assertEqual(args[0].value, part.value)
        self.assertEqual(args[0].quality, part.quality)
        self.assertNotEqual(args[0].id, part.id)

        self.assert_last_scheduled_event(2, source.id, source._finish_processing_part,
                                         EventType.FINISH_PROCESSING)

    def test_max_produced_parts(self):
        part = Part('n', 10, 3)
        source = Source(sample_part = part, max_produced_parts = 5, cycle_time = 1)
        downstream = MagicMock(spec = Machine)
        downstream.give_part.return_value = True
        source._add_downstream(downstream)
        source.initialize(self.env)

        for i in range (1, 5):
            source._finish_processing_part()
            source._pass_part_downstream()
            self.assertEqual(len(downstream.give_part.call_args_list), i)
            self.assertEqual(source.value, -10 * i)
            self.assertEqual(source.produced_parts, i)
            self.assertEqual(source.cost_of_produced_parts, 10 * i)

        source._finish_processing_part()
        source._pass_part_downstream()
        # 6th part should not have been produced or passed downstream.
        self.assertEqual(source.value, -10 * 5)
        self.assertEqual(source.produced_parts, 5)
        self.assertEqual(source.cost_of_produced_parts, 10 * 5)
        self.assertEqual(len(downstream.give_part.call_args_list), 5)

    def test_zero_cycle_time(self):
        source = Source(cycle_time = 0, sample_part = Part())
        downstream = MagicMock(spec = Machine)
        downstream.give_part.return_value = True
        source._add_downstream(downstream)

        self.env.now = 5
        source.initialize(self.env)
        self.assert_last_scheduled_event(5, source.id, source._pass_part_downstream,
                                         EventType.PASS_PART)
        source._pass_part_downstream()
        downstream.give_part.assert_called_once()


if __name__ == '__main__':
    unittest.main()
