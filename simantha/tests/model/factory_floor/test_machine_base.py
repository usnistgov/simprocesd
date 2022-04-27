from unittest import TestCase
import unittest
from unittest.mock import MagicMock, call

from ... import mock_wrap, add_side_effect_to_class_method
from ....model import Environment, EventType
from ....model.factory_floor import Part
from ....model.factory_floor.machine_base import MachineBase


class MachineBaseTestCase(TestCase):

    def setUp(self):
        self.upstream = [MachineBase(), MachineBase()]
        self.env = MagicMock(spec = Environment)
        self.env.now = 0
        for m in self.upstream:
            m.initialize(self.env)

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
        machine = MachineBase('mb', self.upstream, 10)
        self.assertEqual(machine.name, 'mb')
        self.assertEqual(machine.value, 10)
        self.assertEqual(machine.upstream, self.upstream)
        self.assertEqual(machine.downstream, [])
        self.assertTrue(machine.is_operational)
        self.assertEqual(machine.waiting_for_part_start_time, 0)

    def test_set_upstream(self):
        machine = MachineBase(upstream = self.upstream)
        self.assertEqual(self.upstream[0].downstream, [machine])
        self.assertEqual(self.upstream[1].downstream, [machine])

        new_upstream = [MachineBase()]
        machine.upstream = new_upstream
        self.assertEqual(self.upstream[0].downstream, [])
        self.assertEqual(self.upstream[1].downstream, [])
        self.assertEqual(new_upstream[0].downstream, [machine])

    def test_notify_upstream_of_available_space(self):
        mocked_upstream = mock_wrap(self.upstream)
        machine = MachineBase(upstream = mocked_upstream)
        machine.initialize(self.env)
        machine.notify_upstream_of_available_space()

        for u in mocked_upstream:
            u.space_available_downstream.assert_called_once()

    def test_space_available_downstream(self):
        machine = MachineBase(upstream = self.upstream)
        machine.initialize(self.env)

        machine.space_available_downstream()
        self.env.schedule_event.assert_not_called()

        machine.give_part(Part())
        self.env.schedule_event.assert_called_once()
        machine._pass_part_downstream()
        self.env.schedule_event.assert_called_once()
        self.assertEqual(machine.waiting_for_part_start_time, self.env.now)
        machine.space_available_downstream()
        # Schedule event was called once through give_part, check now
        # that it has been called a total of 2 times.
        self.assertEqual(len(self.env.schedule_event.call_args_list), 2)
        self.assert_last_scheduled_event(self.env.now, machine.id, machine._pass_part_downstream,
                                    EventType.PASS_PART)

    def test_give_part(self):
        part1, part2, part3 = Part(), Part(), Part()
        machine = MachineBase(upstream = self.upstream)
        machine.initialize(self.env)
        # MachineBase will immediately move 1 part to output and accept
        # a second part in the input but will not accept a third part.
        self.assertTrue(machine.give_part(part1))
        self.assertEqual(part1.routing_history, [machine.name])
        self.assertTrue(machine.give_part(part2))
        self.assertEqual(part2.routing_history, [machine.name])
        self.assertFalse(machine.give_part(part3))
        self.assertEqual(part3.routing_history, [])

    def test_give_part_when_not_operational(self):
        part = Part()
        machine = MachineBase(upstream = self.upstream)
        machine.initialize(self.env)
        # Make machine return that it is not operational.
        add_side_effect_to_class_method(self, __name__ + '.MachineBase.is_operational',
                                        lambda s: False)

        self.assertFalse(machine.give_part(part))
        self.assertEqual(part.routing_history, [])

    def test_pass_part_downstream(self):
        part = Part()
        mocked_upstream = mock_wrap(self.upstream)
        machine = MachineBase(upstream = mocked_upstream)
        machine.initialize(self.env)
        downstream = MagicMock(spec = MachineBase)
        machine._add_downstream(downstream)

        machine._pass_part_downstream()
        # Check pass part when no part available.
        downstream.give_part.assert_not_called()
        for u in mocked_upstream:
            u.space_available_downstream.assert_not_called()

        machine.give_part(part)
        machine._pass_part_downstream()
        # Check that a part is passed when a part is available.
        downstream.give_part.assert_called_once_with(part)
        for u in mocked_upstream:
            u.space_available_downstream.assert_called_once()

        machine._pass_part_downstream()
        # Check that the part does not get passed a second time.
        downstream.give_part.assert_called_once()
        for u in mocked_upstream:
            u.space_available_downstream.assert_called_once()

    def test_pass_part_downstream_multiple_downstreams(self):
        part = Part()
        mocked_upstream = mock_wrap(self.upstream)
        machine = MachineBase(upstream = mocked_upstream)
        machine.initialize(self.env)
        downstream1 = MagicMock(spec = MachineBase)
        machine._add_downstream(downstream1)
        downstream1.give_part.return_value = False
        # No valid downstream to pass part to.
        machine.give_part(part)
        machine._pass_part_downstream()
        downstream1.give_part.assert_called_once_with(part)
        # New downstream available that can accept the part.
        downstream2 = MagicMock(spec = MachineBase)
        machine._add_downstream(downstream2)
        machine._pass_part_downstream()
        calls = [call(part), call(part)]
        downstream1.give_part.assert_has_calls(calls)
        downstream2.give_part.assert_called_once_with(part)


if __name__ == '__main__':
    unittest.main()
