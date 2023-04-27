from unittest import TestCase
import unittest
from unittest.mock import MagicMock, call

from ... import mock_wrap, add_side_effect_to_class_method
from ....model import Environment, EventType, System
from ....model.factory_floor import Part
from ....model.factory_floor.device import Device


class DeviceTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.upstream = [Device(), Device()]
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
        device = Device('mb', self.upstream, 10)
        self.assertIn(device, self.sys._assets)
        device.initialize(self.env)
        self.assertEqual(device.name, 'mb')
        self.assertEqual(device.value, 10)
        self.assertEqual(device.upstream, self.upstream)
        self.assertEqual(device.downstream, [])
        self.assertTrue(device.is_operational)
        self.assertEqual(device.waiting_for_part_start_time, 0)

    def test_re_initialize(self):
        device = Device('mb', self.upstream, 10)
        device.initialize(self.env)

        for i in range(5):
            part = Part()
            device.give_part(part)
            device.add_value('', 3)
            device.set_upstream([])
            self.assertEqual(device._output, part)
            self.assertEqual(device.value, 10 + 3)
            self.assertEqual(device.upstream, [])
            self.assertEqual(device.waiting_for_part_start_time, None)

            device.initialize(self.env)
            self.assertEqual(device._output, None)
            self.assertEqual(device.value, 10)
            self.assertEqual(device.upstream, self.upstream)
            self.assertEqual(device.waiting_for_part_start_time, 0)

    def test_set_upstream(self):
        device = Device(upstream = self.upstream)
        device.initialize(self.env)
        self.assertEqual(self.upstream[0].downstream, [device])
        self.assertEqual(self.upstream[1].downstream, [device])
        self.assertEqual(device.waiting_for_part_start_time, 0)

        self.env.now = 10
        new_upstream = [Device()]
        device.set_upstream(new_upstream)

        self.assertEqual(self.upstream[0].downstream, [])
        self.assertEqual(self.upstream[1].downstream, [])
        self.assertEqual(new_upstream[0].downstream, [device])
        self.assertEqual(device.waiting_for_part_start_time, 10)

    def test_set_bad_upstreams(self):
        self.assertRaises(TypeError, lambda: Device(upstream = [Part()]))
        device = Device()

        def test_helper():
            device.set_upstream([device])

        self.assertRaises(AssertionError, test_helper)

    def test_notify_upstream_of_available_space(self):
        mocked_upstream = mock_wrap(self.upstream)
        device = Device(upstream = mocked_upstream)
        device.initialize(self.env)
        device.notify_upstream_of_available_space()

        for u in mocked_upstream:
            u.space_available_downstream.assert_called_once()

    def test_space_available_downstream(self):
        device = Device(upstream = self.upstream)
        device.initialize(self.env)

        device.space_available_downstream()
        self.env.schedule_event.assert_not_called()

        device.give_part(Part())
        self.env.schedule_event.assert_called_once()
        # Part will not be passed because downstream was not defined.
        device._pass_part_downstream()
        self.assertEqual(device.waiting_for_part_start_time, None)

        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        device.space_available_downstream()
        self.assertEqual(len(self.env.schedule_event.call_args_list), 2)
        self.assert_last_scheduled_event(self.env.now, device.id, device._pass_part_downstream,
                                    EventType.PASS_PART)

    def test_give_part(self):
        part1, part2 = Part(), Part()
        device = Device(upstream = self.upstream)
        device.initialize(self.env)
        # Device can only hold 1 part at a time.
        self.assertTrue(device.give_part(part1))
        self.assertEqual(part1.routing_history, [device])
        self.assertFalse(device.give_part(part2))
        self.assertEqual(part2.routing_history, [])

    def test_receive_part_callback(self):
        part = Part()
        device = Device(upstream = self.upstream)
        device.initialize(self.env)
        received_part_cb = MagicMock()
        device.add_receive_part_callback(received_part_cb)

        received_part_cb.assert_not_called()
        device.give_part(part)
        received_part_cb.assert_called_once_with(device, part)

    def test_give_part_when_not_operational(self):
        part = Part()
        device = Device(upstream = self.upstream)
        device.initialize(self.env)
        # Make device return that it is not operational.
        add_side_effect_to_class_method(self, __name__ + '.Device.is_operational',
                                        lambda s: False)

        self.assertFalse(device.give_part(part))
        self.assertEqual(part.routing_history, [])

    def test_pass_part_downstream(self):
        part = Part()
        mocked_upstream = mock_wrap(self.upstream)
        device = Device(upstream = mocked_upstream)
        device.initialize(self.env)
        downstream = MagicMock(spec = Device)
        device._add_downstream(downstream)

        device._pass_part_downstream()
        # Check pass part when no part available.
        downstream.give_part.assert_not_called()
        for u in mocked_upstream:
            u.space_available_downstream.assert_not_called()

        device.give_part(part)
        device._pass_part_downstream()
        # Check that a part is passed when a part is available.
        downstream.give_part.assert_called_once_with(part)
        for u in mocked_upstream:
            u.space_available_downstream.assert_called_once()

        device._pass_part_downstream()
        # Check that a part does not get passed a second time.
        downstream.give_part.assert_called_once()
        for u in mocked_upstream:
            u.space_available_downstream.assert_called_once()

    def test_pass_part_downstream_when_one_downstream_blocked(self):
        part = Part()
        mocked_upstream = mock_wrap(self.upstream)
        device = Device(upstream = mocked_upstream)
        device.initialize(self.env)

        downstream1 = MagicMock(spec = Device)
        downstream1.waiting_for_part_start_time = 0
        device._add_downstream(downstream1)
        downstream1.give_part.return_value = False
        # No valid downstream to pass part to.
        device.give_part(part)
        device._pass_part_downstream()
        downstream1.give_part.assert_called_once_with(part)
        # New downstream available that can accept the part.
        downstream2 = MagicMock(spec = Device)
        downstream2.waiting_for_part_start_time = 0
        device._add_downstream(downstream2)
        device._pass_part_downstream()
        calls = [call(part), call(part)]
        downstream1.give_part.assert_has_calls(calls)
        downstream2.give_part.assert_called_once_with(part)

    def test_pass_part_downstream_order(self):
        device = Device()
        device.initialize(self.env)
        downstreams = []
        for i in range(3):
            downstreams.append(MagicMock(spec = Device))
            downstreams[-1].give_part.return_value = True
            downstreams[-1].waiting_for_part_start_time = i
            device._add_downstream(downstreams[-1])

        device.give_part(Part())
        device._pass_part_downstream()
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 1)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 0)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 0)

        downstreams[0].waiting_for_part_start_time = 4
        downstreams[1].waiting_for_part_start_time = 6
        device.give_part(Part())
        device._pass_part_downstream()
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 1)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 0)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 1)

        downstreams[2].waiting_for_part_start_time = 10
        device.give_part(Part())
        device._pass_part_downstream()
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 2)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 0)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 1)
        # None means device is not marked as waiting for parts yet.
        downstreams[0].waiting_for_part_start_time = None
        device.give_part(Part())
        device._pass_part_downstream()
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 2)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 1)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 1)

    def test_downstream_priority_sorter(self):
        downstreams = []
        downstreams.append(MagicMock(spec = Device))
        downstreams[-1].waiting_for_part_start_time = None
        for i in range(3):
            downstreams.append(MagicMock(spec = Device))
            downstreams[-1].waiting_for_part_start_time = 10 - i

        sorted_ds = Device.downstream_priority_sorter(downstreams)
        self.assertEqual(sorted_ds[0].waiting_for_part_start_time, 8)
        self.assertEqual(sorted_ds[1].waiting_for_part_start_time, 9)
        self.assertEqual(sorted_ds[2].waiting_for_part_start_time, 10)
        self.assertEqual(sorted_ds[3].waiting_for_part_start_time, None)


if __name__ == '__main__':
    unittest.main()
