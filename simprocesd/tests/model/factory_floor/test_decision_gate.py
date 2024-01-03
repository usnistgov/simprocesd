from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, System
from ....model.factory_floor import Part, PartHandler, DecisionGate


class DecisionGateTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 1
        self.upstream = [MagicMock(spec = PartHandler), MagicMock(spec = PartHandler)]
        for u in self.upstream:
            u.joined_group = None
        self.downstream = [MagicMock(spec = PartHandler), MagicMock(spec = PartHandler)]
        for d in self.downstream:
            d.give_part.return_value = True
            d.waiting_for_part_start_time = None

    def test_initialize(self):
        gate = DecisionGate('name', self.upstream, lambda gate, part: True)
        self.assertIn(gate, self.sys._assets)
        self.assertEqual(gate.name, 'name')
        self.assertCountEqual(gate.upstream, self.upstream)
        self.assertEqual(gate.value, 0)

    def test_notify_upstream_of_available_space(self):
        gate = DecisionGate('name', self.upstream, lambda g, p: True)

        for u in self.upstream:
            u.space_available_downstream.assert_not_called()
        gate.space_available_downstream()
        for u in self.upstream:
            u.space_available_downstream.assert_called_once()

    def test_pass_part(self):
        gate = DecisionGate(decider_override = lambda g, p: True)
        gate._add_downstream(self.downstream[0])
        part = Part()

        self.assertTrue(gate.give_part(part))
        # Ensure no events are generated.
        self.assertEqual(len(self.env.schedule_event.call_args_list), 0)
        self.downstream[0].give_part.assert_called_once_with(part)

    def test_pass_part_condition(self):
        gate = DecisionGate(decider_override = lambda g, p: g == gate and p.value > 1)
        for d in self.downstream:
            gate._add_downstream(d)
        bad_part = Part(value = 0)
        good_part = Part(value = 2)

        self.assertFalse(gate.give_part(bad_part))
        self.downstream[0].give_part.assert_not_called()
        self.downstream[1].give_part.assert_not_called()

        self.assertTrue(gate.give_part(good_part))
        self.downstream[0].give_part.assert_called_once_with(good_part)
        self.downstream[1].give_part.assert_not_called()

    def test_pass_part_blocked_downstream(self):
        gate = DecisionGate(decider_override = lambda g, p: True)
        for d in self.downstream:
            gate._add_downstream(d)
        part1, part2 = Part(), Part()
        # First downstream does not accept part but second does.
        self.downstream[0].give_part.return_value = False
        self.assertTrue(gate.give_part(part1))
        self.downstream[0].give_part.assert_called_once_with(part1)
        self.downstream[1].give_part.assert_called_once_with(part1)
        # Neither downstream will accept the part.
        self.downstream[1].give_part.return_value = False
        self.assertFalse(gate.give_part(part2))
        self.assertEqual(len(self.downstream[0].give_part.call_args_list), 2)
        self.assertEqual(len(self.downstream[1].give_part.call_args_list), 2)

    def test_no_decider(self):
        gate = DecisionGate()
        self.assertRaises(NotImplementedError, lambda: gate.give_part(Part()))

    def test_default_decider(self):

        class TestDG(DecisionGate):

            def part_pass_decider(self, part):
                return part.name == 'a'

        gate = TestDG()
        for d in self.downstream:
            gate._add_downstream(d)
        part1, part2 = Part('a'), Part('b')

        self.assertTrue(gate.give_part(part1))
        self.assertFalse(gate.give_part(part2))


if __name__ == '__main__':
    unittest.main()
