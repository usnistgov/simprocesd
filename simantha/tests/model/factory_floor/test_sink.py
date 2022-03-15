from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ... import mock_wrap
from ....model import Environment, EventType
from ....model.factory_floor import Part, Machine, Sink


class SinkTestCase(TestCase):

    def setUp(self):
        self.env = MagicMock(spec = Environment)
        self.env.now = 3

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
        upstream = [Machine()]
        sink = Sink('name', upstream, 4, True)
        self.assertEqual(sink.name, 'name')
        self.assertEqual(sink.upstream, upstream)
        self.assertEqual(sink.value, 0)
        self.assertEqual(sink.received_parts_count, 0)
        self.assertEqual(sink.value_of_received_parts, 0)
        self.assertEqual(sink.collected_parts, [])

    def test_add_downstream(self):
        sink = Sink()
        self.assertRaises(RuntimeError, lambda: Machine(upstream = [sink]))

    def test_collect_parts(self):
        part = Part()
        sink = Sink('', [], 0, False)
        sink.initialize(self.env)
        sink.give_part(part)
        self.assertEqual(sink.collected_parts, [])

        sink = Sink('', [], 0, True)
        sink.initialize(self.env)
        sink.give_part(part)
        self.assertEqual(sink.collected_parts, [part])

    def test_receive_part(self):
        part = Part(value = 2.5)
        upstream = [mock_wrap(Machine())]
        sink = Sink('', upstream, 4, True)
        sink.initialize(self.env)

        self.assertTrue(sink.give_part(part))
        self.assert_last_scheduled_event(3 + 4, sink.id, sink._finish_processing_part,
                                         EventType.FINISH_PROCESSING)
        self.assertEqual(part.routing_history, [sink.name])
        upstream[0].space_available_downstream.assert_not_called()
        self.assertEqual(sink.value, 2.5)
        self.assertEqual(sink.received_parts_count, 1)
        self.assertEqual(sink.value_of_received_parts, 2.5)
        self.assertCountEqual(sink.collected_parts, [part])
        # Second part should not be accepted yet.
        self.assertFalse(sink.give_part(Part()))

        sink._finish_processing_part()
        upstream[0].space_available_downstream.assert_called_once()
        self.assertTrue(sink.give_part(Part()))

    def test_receive_many_parts(self):
        sink = Sink('', [], 4, True)
        sink.initialize(self.env)
        parts = []
        for i in range(5):
            parts.append(Part(value = 2.5))
            self.assertTrue(sink.give_part(parts[i]))
            self.assertCountEqual(sink.collected_parts, parts)
            self.assertEqual(sink.value, 2.5 * (i + 1))
            self.assertEqual(sink.received_parts_count, i + 1)
            self.assertEqual(sink.value_of_received_parts, 2.5 * (i + 1))
            sink._finish_processing_part()


if __name__ == '__main__':
    unittest.main()
