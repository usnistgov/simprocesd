from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ... import mock_wrap
from ....model import Environment, EventType, System
from ....model.factory_floor import Part, PartGenerator, PartProcessor, Source


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
        source = Source('name', PartGenerator(''), 2, 15)
        self.assertEqual(source.name, 'name')
        self.assertEqual(source.value, 0)
        self.assertEqual(source.upstream, [])
        self.assertEqual(source.produced_parts, 0)
        self.assertEqual(source.cost_of_produced_parts, 0)
        self.assertEqual(source.cycle_time, 2)
        self.assertIn(source, self.sys._assets)

    def test_initialize(self):
        source = Source(part_generator = PartGenerator('', value = 5), cycle_time = 6)
        source.initialize(self.env)
        self.assert_last_scheduled_event(6, source.id, source._finish_cycle,
                                         EventType.FINISH_PROCESSING)

        self.env.now = 6
        source._finish_cycle()
        self.assertEqual(source.value, 0)
        self.assertEqual(source.produced_parts, 0)
        self.assertEqual(source.cost_of_produced_parts, 0)
        self.assert_last_scheduled_event(6, source.id, source._pass_part_downstream,
                                         EventType.PASS_PART)

    def test_upstream(self):
        # Source is not allowed to have upstream machines.
        source = Source()
        self.assertRaises(ValueError, lambda: source.set_upstream([PartProcessor()]))

    def test_pass_part_downstream(self):
        wrapped_pg = mock_wrap(PartGenerator('n', 10, 3))
        source = Source(part_generator = wrapped_pg, cycle_time = 1)
        downstream = MagicMock(spec = PartProcessor)
        downstream.give_part.return_value = True
        source._add_downstream(downstream)

        source.initialize(self.env)
        wrapped_pg.generate_part.assert_not_called()
        self.env.now = 1
        source._finish_cycle()
        wrapped_pg.generate_part.assert_called_once()

        source._pass_part_downstream()
        self.assertEqual(source.value, -10)
        self.assertEqual(source.produced_parts, 1)
        self.assertEqual(source.cost_of_produced_parts, 10)

        args, kwargs = downstream.give_part.call_args
        # arg[0] is the part that was passed with give_part
        self.assertEqual(args[0].name, 'n_1')
        self.assertEqual(args[0].value, 10)
        self.assertEqual(args[0].quality, 3)

        self.assert_last_scheduled_event(2, source.id, source._finish_cycle,
                                         EventType.FINISH_PROCESSING)

    def test_max_produced_parts(self):
        source = Source(part_generator = PartGenerator('n', 10, 3), starting_parts = 5, cycle_time = 1)
        downstream = MagicMock(spec = PartProcessor)
        downstream.give_part.return_value = True
        source._add_downstream(downstream)
        source.initialize(self.env)

        for i in range (1, 5):
            source._finish_cycle()
            source._pass_part_downstream()
            self.assertEqual(len(downstream.give_part.call_args_list), i)
            self.assertEqual(source.value, -10 * i)
            self.assertEqual(source.produced_parts, i)
            self.assertEqual(source.cost_of_produced_parts, 10 * i)
            self.assertEqual(source.remaining_parts, 5 - i)

        source._finish_cycle()
        source._pass_part_downstream()
        # 6th part should not have been produced or passed downstream.
        self.assertEqual(source.value, -10 * 5)
        self.assertEqual(source.produced_parts, 5)
        self.assertEqual(source.cost_of_produced_parts, 10 * 5)
        self.assertEqual(len(downstream.give_part.call_args_list), 5)

    def test_zero_cycle_time(self):
        source = Source(cycle_time = 0)
        downstream = MagicMock(spec = PartProcessor)
        downstream.give_part.return_value = True
        source._add_downstream(downstream)

        self.env.now = 5
        source.initialize(self.env)
        self.assert_last_scheduled_event(5, source.id, source._pass_part_downstream,
                                         EventType.PASS_PART)
        source._pass_part_downstream()
        downstream.give_part.assert_called_once()

    def test_adjust_part_count(self):
        source = Source(starting_parts = 5)
        downstream = MagicMock(spec = PartProcessor)
        downstream.give_part.return_value = True
        source._add_downstream(downstream)
        source.initialize(self.env)
        self.assertEqual(source.remaining_parts, 5)

        source.adjust_part_count(3)
        self.assertEqual(source.remaining_parts, 8)
        source.adjust_part_count(-6)
        self.assertEqual(source.remaining_parts, 2)

        source._finish_cycle()
        source._pass_part_downstream()
        self.assertEqual(source.produced_parts, 1)
        self.assertEqual(source.remaining_parts, 1)

        source.adjust_part_count(-6)
        self.assertEqual(source.remaining_parts, 0)
        source._finish_cycle()
        source._pass_part_downstream()
        self.assertEqual(source.produced_parts, 1)
        self.assertEqual(source.remaining_parts, 0)

        source.adjust_part_count(42)
        self.assertEqual(source.remaining_parts, 42)


if __name__ == '__main__':
    unittest.main()
