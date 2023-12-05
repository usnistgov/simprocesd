from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, System
from ....model.factory_floor import Part, Group, PartFlowController, PartHandler, PartProcessor
from ... import mock_wrap


class PartTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 0
        self.downstream = MagicMock(spec = PartFlowController)
        self.downstream.give_part.return_value = True

    def reset_joined_groups(self, devices):
        for d in devices:
            d._joined_groups = []

    def test_create_group(self):
        devices = []
        for i in range(5):
            devices.append(PartFlowController())
        group = Group('the name', devices)
        self.assertEqual(group.name, 'the name')

    def test_invalid_groups(self):
        self.assertRaises(TypeError, lambda: Group('', [PartFlowController(), Part()]))

        d1 = PartFlowController()
        d2 = PartHandler(upstream = [d1])
        d3 = PartProcessor(upstream = [d2])
        self.assertRaises(ValueError, lambda: Group('', [d1]))
        self.reset_joined_groups([d1, d2, d3])
        self.assertRaises(ValueError, lambda: Group('', [d2]))
        self.reset_joined_groups([d1, d2, d3])
        self.assertRaises(ValueError, lambda: Group('', [d3]))
        self.reset_joined_groups([d1, d2, d3])
        self.assertRaises(ValueError, lambda: Group('', [d1, d2]))
        self.reset_joined_groups([d1, d2, d3])
        self.assertRaises(ValueError, lambda: Group('', [d2, d3]))
        self.reset_joined_groups([d1, d2, d3])
        self.assertRaises(ValueError, lambda: Group('', [d1, d3]))
        self.reset_joined_groups([d1, d2, d3])

        # Valid case, no error.
        Group('name', [d1, d2, d3])

    def test_make_group_path(self):
        upstream = MagicMock(spec = PartFlowController)
        group_device = PartHandler()
        group = Group('', [group_device])
        group_path1 = group.get_new_group_path('gp1', [upstream])
        self.assertEqual(group_path1.name, 'gp1')
        self.assertEqual(group_path1.upstream, [upstream])
        group_path2 = group.get_new_group_path('gp2', [])
        self.assertEqual(group_path2.name, 'gp2')
        self.assertEqual(group_path2.upstream, [])

    def test_part_flow(self):
        group_device1 = PartHandler()
        group_device2 = PartHandler(upstream = [group_device1])
        group = Group('', [group_device1, group_device2])
        gp = group.get_new_group_path('name', [])
        downstream = PartHandler(upstream = [gp])
        self.sys._initialize_assets()

        part = Part()
        self.assertTrue(gp.give_part(part))
        self.assertEqual(group_device1._part, None)
        self.assertEqual(group_device1._output, part)
        self.assertEqual(group_device2._part, None)
        self.assertEqual(group_device2._output, None)
        self.assertEqual(downstream._part, None)
        self.assertEqual(downstream._output, None)
        self.assertEqual(part.routing_history, [gp, group_device1])

        group_device1._pass_part_downstream()
        self.assertEqual(group_device1._part, None)
        self.assertEqual(group_device1._output, None)
        self.assertEqual(group_device2._part, None)
        self.assertEqual(group_device2._output, part)
        self.assertEqual(downstream._part, None)
        self.assertEqual(downstream._output, None)
        self.assertEqual(part.routing_history, [gp, group_device1, group_device2])

        group_device2._pass_part_downstream()
        self.assertEqual(group_device1._part, None)
        self.assertEqual(group_device1._output, None)
        self.assertEqual(group_device2._part, None)
        self.assertEqual(group_device2._output, None)
        self.assertEqual(downstream._part, None)
        self.assertEqual(downstream._output, part)
        self.assertEqual(part.routing_history, [gp, group_device1, group_device2, downstream])

    def test_pass_notification_of_available_space(self):
        tracker = MagicMock()
        group_device = PartHandler()
        group_device.space_available_downstream = lambda: tracker.space_available_downstream()
        group = Group('', [group_device])
        upstream = MagicMock(spec = PartHandler)
        gp = group.get_new_group_path('name', [upstream])
        downstream = PartHandler(upstream = [gp])
        self.sys._initialize_assets()

        tracker.space_available_downstream.assert_not_called()
        downstream.notify_upstream_of_available_space()
        tracker.space_available_downstream.assert_called_once()

        upstream.space_available_downstream.assert_not_called()
        group_device.notify_upstream_of_available_space()
        upstream.space_available_downstream.assert_called_once()

    def test_input_override(self):
        # 4 devices in 2 stages
        group_devices = [PartHandler() for i in range(3)]
        group = Group('', group_devices, input_override = group_devices[0:2])
        gp = group.get_new_group_path('name', [])
        self.sys._initialize_assets()

        part1, part2 = Part('p1'), Part('p2')
        self.assertTrue(gp.give_part(part1))
        self.assertTrue(gp.give_part(part2))
        # Third device is not configured as an input.
        self.assertFalse(gp.give_part(Part()))

        self.assertTrue(group_devices[0]._output == part1 or group_devices[0]._output == part2,
                        f'Device should have part1 or part2 but had: {group_devices[0]._output}')
        self.assertTrue(group_devices[1]._output == part1 or group_devices[1]._output == part2,
                        f'Device should have part1 or part2 but had: {group_devices[1]._output}')

    def test_output_override(self):
        # 4 devices in 2 stages
        group_devices = [PartHandler() for i in range(3)]
        group = Group('', group_devices, input_override = group_devices,
                                         output_override = group_devices[0:2])
        gp = group.get_new_group_path('name', [])
        downstream = PartHandler(upstream = [gp])
        self.sys._initialize_assets()

        self.assertTrue(gp.give_part(Part()))
        self.assertTrue(gp.give_part(Part()))
        self.assertTrue(gp.give_part(Part()))

        part = group_devices[0]._output
        self.assertNotEqual(part, None)
        group_devices[0]._pass_part_downstream()
        self.assertEqual(downstream._output, part)
        downstream._output = None

        part = group_devices[1]._output
        self.assertNotEqual(part, None)
        group_devices[1]._pass_part_downstream()
        self.assertEqual(downstream._output, part)
        downstream._output = None

        # Third device is not configured as an output.
        part = group_devices[2]._output
        self.assertNotEqual(part, None)
        group_devices[2]._pass_part_downstream()
        self.assertEqual(downstream._output, None)


if __name__ == '__main__':
    unittest.main()
