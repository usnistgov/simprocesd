from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ... import add_side_effect_to_class_method
from ....model import Environment
from ....model.factory_floor import Part, Machine, PartHandlingDevice, FlowOrder


class PartHandlingDeviceTestCase(TestCase):

    @staticmethod
    def fake_shuffle(list_):
        ''' Shuffle will move an element from the front of the list to
        the back, this will be done N times. N is the number of times
        shuffle was called during current test, N = 1 for first call.
        '''
        PartHandlingDeviceTestCase.shuffle_count += 1
        for i in range(PartHandlingDeviceTestCase.shuffle_count):
            list_.append(list_.pop(0))

    def setUp(self):
        self.env = MagicMock(spec = Environment)
        self.env.now = 1
        self.upstream = [MagicMock(spec = Machine), MagicMock(spec = Machine)]
        self.downstream = []
        for i in range(5):
            self.downstream.append(MagicMock(spec = Machine))
            self.downstream[i].give_part.return_value = True
        # Mock out random.shuffle to move first element to the end.
        self.shuffle_mock = add_side_effect_to_class_method(self, 'random.shuffle',
                                                            PartHandlingDeviceTestCase.fake_shuffle)
        PartHandlingDeviceTestCase.shuffle_count = 0

    def test_initialize(self):
        phd = PartHandlingDevice('name', self.upstream, FlowOrder.RANDOM)
        self.assertEqual(phd.name, 'name')
        self.assertEqual(phd.upstream, self.upstream)
        self.assertEqual(phd.downstream, [])
        self.assertEqual(phd.value, 0)

    def test_notify_upstream_of_available_space(self):
        phd = PartHandlingDevice(upstream = self.upstream)

        for u in self.upstream:
            u.space_available_downstream.assert_not_called()
        phd.space_available_downstream()
        for u in self.upstream:
            u.space_available_downstream.assert_called_once()

    def test_set_downstream(self):
        phd = PartHandlingDevice()
        for d in self.downstream:
            phd._add_downstream(d)
        self.assertEqual(phd.downstream, self.downstream)

        expected_downstream = self.downstream.copy()
        # Change the order by removing first element and appending it to
        # the end.
        expected_downstream.append(expected_downstream.pop(0))
        phd.set_downstream_order(expected_downstream)
        self.assertEqual(phd.downstream, expected_downstream)
        # Now add a new downstream and try to set it again.
        extra_downstream = MagicMock(spec = Machine)
        phd._add_downstream(extra_downstream)
        expected_downstream = self.downstream.copy()
        expected_downstream.append(extra_downstream)
        phd.set_downstream_order(expected_downstream)
        self.assertEqual(phd.downstream, expected_downstream)

    def test_set_different_downstream(self):
        phd = PartHandlingDevice()
        for d in self.downstream:
            phd._add_downstream(d)
        new_downstream = []

        def helper(): phd.set_downstream_order(new_downstream)

        # Sanity check that normal call does not raise an error.
        new_downstream = self.downstream.copy()
        helper()
        # Test last element is different.
        new_downstream = self.downstream.copy()
        new_downstream[-1] = MagicMock(spec = Machine)
        self.assertRaises(AssertionError, helper)
        # Test missing an element.
        new_downstream = self.downstream.copy()
        new_downstream.pop(2)
        self.assertRaises(AssertionError, helper)
        # Test extra element.
        new_downstream = self.downstream.copy()
        new_downstream.append(MagicMock(spec = Machine))
        self.assertRaises(AssertionError, helper)

    def test_pass_part(self):
        phd = PartHandlingDevice()
        phd._add_downstream(self.downstream[0])
        part = Part()

        self.assertTrue(phd.give_part(part))
        # Ensure no events are generated.
        self.assertEqual(len(self.env.schedule_event.call_args_list), 0)
        self.downstream[0].give_part.assert_called_once_with(part)

    def test_pass_part_round_robin(self):
        phd = PartHandlingDevice(flow_order = FlowOrder.ROUND_ROBIN)
        for d in self.downstream:
            phd._add_downstream(d)

        parts = []
        for i in range(10):
            parts.append(Part())
            self.assertTrue(phd.give_part(parts[i]))
            expected_receiver = self.downstream[i % len(self.downstream)]
            self.assertEqual(expected_receiver.give_part.call_args[0][0], parts[i])

    def test_pass_part_round_robin_with_block(self):
        phd = PartHandlingDevice(flow_order = FlowOrder.ROUND_ROBIN)
        for d in self.downstream:
            phd._add_downstream(d)
        self.downstream[2].give_part.return_value = False
        # Remove downstream from list as it will not accept parts.
        blocked_downstream = self.downstream.pop(2)

        parts = []
        for i in range(10):
            parts.append(Part())
            self.assertTrue(phd.give_part(parts[i]))
            expected_receiver = self.downstream[i % len(self.downstream)]
            # If expected downstream is right after blocked downstream in the list.
            if expected_receiver == self.downstream[2]:
                self.assertEqual(blocked_downstream.give_part.call_args[0][0], parts[i])
            self.assertEqual(expected_receiver.give_part.call_args[0][0], parts[i])

    def test_pass_part_first_available(self):
        phd = PartHandlingDevice(flow_order = FlowOrder.FIRST_AVAILABLE)
        for d in self.downstream:
            phd._add_downstream(d)

        parts = []
        for i in range(10):
            parts.append(Part())
            self.assertTrue(phd.give_part(parts[i]))
            expected_receiver = self.downstream[0]
            self.assertEqual(expected_receiver.give_part.call_args[0][0], parts[i])

    def test_pass_part_first_available_with_block(self):
        phd = PartHandlingDevice(flow_order = FlowOrder.FIRST_AVAILABLE)
        for d in self.downstream:
            phd._add_downstream(d)
        self.downstream[0].give_part.return_value = False
        blocked_downstream = self.downstream[0]

        parts = []
        for i in range(10):
            parts.append(Part())
            self.assertTrue(phd.give_part(parts[i]))
            expected_receiver = self.downstream[1]
            self.assertEqual(blocked_downstream.give_part.call_args[0][0], parts[i])
            self.assertEqual(expected_receiver.give_part.call_args[0][0], parts[i])

    def test_pass_part_random(self):
        phd = PartHandlingDevice(flow_order = FlowOrder.RANDOM)
        for d in self.downstream:
            phd._add_downstream(d)

        parts = []
        for i in range(10):
            parts.append(Part())
            self.assertTrue(phd.give_part(parts[i]))
            # Based on PartHandlingDeviceTestCase.fake_shuffle.
            expected_receiver = self.downstream[(i + 1) % len(self.downstream)]
            self.assertEqual(expected_receiver.give_part.call_args[0][0], parts[i])

    def test_pass_part_random_with_block(self):
        phd = PartHandlingDevice(flow_order = FlowOrder.RANDOM)
        for d in self.downstream:
            phd._add_downstream(d)
        self.downstream[0].give_part.return_value = False
        # Remove downstream from list as it will not accept parts.
        blocked_downstream = self.downstream[0]

        parts = []
        for i in range(10):
            parts.append(Part())
            self.assertTrue(phd.give_part(parts[i]))
            # Based on PartHandlingDeviceTestCase.fake_shuffle.
            expected_receiver = self.downstream[(i + 1) % len(self.downstream)]
            if expected_receiver == blocked_downstream:
                self.assertEqual(blocked_downstream.give_part.call_args[0][0], parts[i])
                # If first element is blocked then the next element in
                # the blocked list will be tried.
                expected_receiver = self.downstream[(i + 2) % len(self.downstream)]
            # Blocked downstream will be called with every part.
            self.assertEqual(expected_receiver.give_part.call_args[0][0], parts[i])


if __name__ == '__main__':
    unittest.main()
