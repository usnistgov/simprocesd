from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, System, EventType
from ....model.factory_floor import Part, Machine, PartBatcher, Batch


class PartBatcherTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 1
        self.upstream = [MagicMock(spec = Machine)]
        self.downstream = [MagicMock(spec = Machine), MagicMock(spec = Machine)]
        for d in self.downstream:
            d.give_part.return_value = True

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
        pb = PartBatcher('name', self.upstream, 10, 2)
        pb.initialize(self.env)
        self.assertIn(pb, self.sys._assets)
        self.assertEqual(pb.name, 'name')
        self.assertCountEqual(pb.upstream, self.upstream)
        self.assertEqual(pb.value, 10)

    def test_single_part_output(self):
        pb = PartBatcher(output_batch_size = None)
        for d in self.downstream:
            pb._add_downstream(d)
        pb.initialize(self.env)

        for i in range(5):
            part = Part()
            part.initialize(self.env)
            pb.give_part(part)
            pb._try_move_part_to_output()
            self.assert_last_scheduled_event(self.env.now, pb.id, pb._pass_part_downstream,
                                             EventType.PASS_PART)
            self.assertEqual(pb._output, part)
            pb._output = None
            self.env.now += 1
            # Ensure there are no extra Parts.
            pb._try_move_part_to_output()
            self.assertEqual(pb._output, None)

        for i in range(3):
            batch = Batch(parts = [Part(), Part()])
            batch.initialize(self.env)
            pb.give_part(batch)
            # Once for each Part in the Batch.
            for i in range(2):
                pb._try_move_part_to_output()
                self.assert_last_scheduled_event(self.env.now, pb.id, pb._pass_part_downstream,
                                                 EventType.PASS_PART)
                self.assertNotEqual(pb._output, None)
                pb._output = None
                self.env.now += 1
            # Ensure there are no extra Parts.
            pb._try_move_part_to_output()
            self.assertEqual(pb._output, None)

    def test_batch_output(self):
        pb = PartBatcher(output_batch_size = 2)
        for d in self.downstream:
            pb._add_downstream(d)
        pb.initialize(self.env)

        for i in range(5):
            part1, part2 = Part(), Part()
            part1.initialize(self.env)
            part2.initialize(self.env)
            pb.give_part(part1)
            pb._try_move_part_to_output()
            # First Part should not trigger output which requires 2 Parts.
            self.assertEqual(pb._output, None)
            pb.give_part(part2)
            pb._try_move_part_to_output()
            self.assert_last_scheduled_event(self.env.now, pb.id, pb._pass_part_downstream,
                                             EventType.PASS_PART)
            self.assertIsInstance(pb._output, Batch)
            self.assertCountEqual(pb._output.parts, [part1, part2])
            pb._output = None
            self.env.now += 1
            # Ensure there are no extra Parts.
            pb._try_move_part_to_output()
            self.assertEqual(pb._output, None)

        for i in range(3):
            part1, part2 = Part(), Part()
            batch = Batch(parts = [part1, part2])
            batch.initialize(self.env)
            pb.give_part(batch)
            pb._try_move_part_to_output()
            self.assert_last_scheduled_event(self.env.now, pb.id, pb._pass_part_downstream,
                                             EventType.PASS_PART)
            self.assertIsInstance(pb._output, Batch)
            self.assertNotEqual(pb._output, batch)
            self.assertCountEqual(pb._output.parts, [part1, part2])
            pb._output = None
            self.env.now += 1
            # Ensure there are no extra Parts.
            pb._try_move_part_to_output()
            self.assertEqual(pb._output, None)


if __name__ == '__main__':
    unittest.main()
