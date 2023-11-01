from unittest import TestCase
import unittest
from unittest.mock import MagicMock, call

from ... import mock_wrap
from ....model import Environment, System
from ....model.factory_floor import Part, PartFlowController


class PartFlowControllerTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.upstream = [PartFlowController(), PartFlowController()]
        self.env = MagicMock(spec = Environment)
        self.env.now = 0
        for m in self.upstream:
            m.initialize(self.env)

    def add_downstream(self, target, give_part_return = True, waiting_for_part_start_time = 0):
        downstream = MagicMock(spec = PartFlowController)
        downstream.give_part.return_value = give_part_return
        downstream.waiting_for_part_start_time = waiting_for_part_start_time
        if target != None:
            target._add_downstream(downstream)
        return downstream

    def test_initialize(self):
        pfc = PartFlowController('mb', self.upstream, 10)
        self.assertIn(pfc, self.sys._assets)
        pfc.initialize(self.env)
        self.assertEqual(pfc.name, 'mb')
        self.assertEqual(pfc.value, 10)
        self.assertEqual(pfc.upstream, self.upstream)
        self.assertEqual(pfc.downstream, [])
        self.assertTrue(pfc.is_operational)
        self.assertEqual(pfc.waiting_for_part_start_time, None)
        self.assertEqual(pfc.block_input, False)

    def test_set_upstream(self):
        pfc = PartFlowController(upstream = self.upstream)
        pfc.initialize(self.env)
        self.assertEqual(self.upstream[0].downstream, [pfc])
        self.assertEqual(self.upstream[1].downstream, [pfc])

        self.env.now = 10
        new_upstream = [PartFlowController()]
        pfc.set_upstream(new_upstream)

        self.assertEqual(self.upstream[0].downstream, [])
        self.assertEqual(self.upstream[1].downstream, [])
        self.assertEqual(new_upstream[0].downstream, [pfc])

    def test_set_bad_upstreams(self):
        self.assertRaises(TypeError, lambda: PartFlowController(upstream = [Part()]))
        pfc = PartFlowController()

        def test_helper():
            pfc.set_upstream([pfc])

        self.assertRaises(AssertionError, test_helper)

    def test_notify_upstream_of_available_space(self):
        mocked_upstream = mock_wrap(self.upstream)
        pfc = PartFlowController(upstream = mocked_upstream)
        pfc.initialize(self.env)
        pfc.notify_upstream_of_available_space()

        for u in mocked_upstream:
            u.space_available_downstream.assert_called_once()

    def test_space_available_downstream(self):
        mocked_upstream = mock_wrap(self.upstream)
        pfc = PartFlowController(upstream = mocked_upstream)
        pfc.initialize(self.env)

        pfc.is_operational = lambda: False
        pfc.space_available_downstream()
        for u in mocked_upstream:
            u.space_available_downstream.assert_not_called()

        pfc.is_operational = lambda: True
        pfc.space_available_downstream()
        for u in mocked_upstream:
            u.space_available_downstream.assert_called_once()

    def test_give_part(self):
        part1, part2 = Part(), Part()
        pfc = PartFlowController(upstream = self.upstream)
        downstream = self.add_downstream(pfc)
        pfc.initialize(self.env)

        downstream.give_part.return_value = True
        self.assertTrue(pfc.give_part(part1))
        self.assertEqual(part1.routing_history, [pfc])

        downstream.give_part.return_value = False
        self.assertFalse(pfc.give_part(part2))
        self.assertEqual(part2.routing_history, [])

    def test_give_part_when_not_operational(self):
        part = Part()
        pfc = PartFlowController(upstream = self.upstream)
        downstream = self.add_downstream(pfc, True, 0)
        pfc.initialize(self.env)

        pfc.is_operational = lambda: False
        self.assertFalse(pfc.give_part(part))
        self.assertEqual(part.routing_history, [])

    def test_pass_part_downstream(self):
        part = Part()
        pfc = PartFlowController()
        pfc.initialize(self.env)
        downstream = self.add_downstream(pfc, True, 0)

        pfc.give_part(part)
        downstream.give_part.assert_called_once_with(part)

    def test_pass_part_downstream_when_one_downstream_blocked(self):
        part = Part()
        mocked_upstream = mock_wrap(self.upstream)
        pfc = PartFlowController(upstream = mocked_upstream)
        pfc.initialize(self.env)

        downstream1 = self.add_downstream(pfc, False, 0)
        # No valid downstream to pass part to.
        pfc.give_part(part)
        downstream1.give_part.assert_called_once_with(part)
        # New downstream available that can accept the part.
        downstream2 = self.add_downstream(pfc, False, 0)
        pfc.give_part(part)
        calls = [call(part), call(part)]
        downstream1.give_part.assert_has_calls(calls)
        downstream2.give_part.assert_called_once_with(part)

    def test_waiting_for_part_start_time(self):
        mocked_upstream = mock_wrap(self.upstream)
        pfc = PartFlowController(upstream = mocked_upstream)
        pfc.initialize(self.env)
        self.env.now = 20
        self.assertEqual(pfc.waiting_for_part_start_time, None)

        downstream1 = self.add_downstream(pfc, True, None)
        downstream2 = self.add_downstream(pfc, True, 3)
        downstream3 = self.add_downstream(pfc, False, 10)
        self.assertEqual(pfc.waiting_for_part_start_time, 3)
        pfc.give_part(Part())
        self.assertEqual(pfc.waiting_for_part_start_time, 3)

        downstream2.waiting_for_part_start_time = 12
        self.assertEqual(pfc.waiting_for_part_start_time, 10)
        downstream2.waiting_for_part_start_time = None
        downstream3.waiting_for_part_start_time = None
        self.assertEqual(pfc.waiting_for_part_start_time, None)

    def test_pass_part_downstream_order(self):
        pfc = PartFlowController()
        pfc.initialize(self.env)
        downstreams = []
        for i in range(3):
            downstreams.append(self.add_downstream(pfc, True, i))

        pfc.give_part(Part())
        # Waiting start times: 0, 1, 2
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 1)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 0)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 0)

        downstreams[0].waiting_for_part_start_time = 4
        downstreams[1].waiting_for_part_start_time = 6
        pfc.give_part(Part())
        # Waiting start times: 4, 6, 2
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 1)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 0)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 1)

        downstreams[2].waiting_for_part_start_time = 10
        pfc.give_part(Part())
        # Waiting start times: 4, 6, 10
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 2)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 0)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 1)
        # None means pfc is not marked as waiting for parts.
        downstreams[0].waiting_for_part_start_time = None
        pfc.give_part(Part())
        # Waiting start times: --, 6, 10
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 2)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 1)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 1)

    def test_downstream_priority_sorter(self):
        downstreams = []
        downstreams.append(MagicMock(spec = PartFlowController))
        downstreams[-1].waiting_for_part_start_time = None
        for i in range(3):
            downstreams.append(MagicMock(spec = PartFlowController))
            downstreams[-1].waiting_for_part_start_time = 10 - i

        sorted_ds = PartFlowController.downstream_priority_sorter(downstreams)
        self.assertEqual(sorted_ds[0].waiting_for_part_start_time, 8)
        self.assertEqual(sorted_ds[1].waiting_for_part_start_time, 9)
        self.assertEqual(sorted_ds[2].waiting_for_part_start_time, 10)
        self.assertEqual(sorted_ds[3].waiting_for_part_start_time, None)

    def test_block_input(self):
        pfc = PartFlowController(upstream = self.upstream)
        downstream = self.add_downstream(pfc, True, 0)
        pfc.initialize(self.env)

        pfc.block_input = True
        self.assertFalse(pfc.give_part(Part()))
        pfc.block_input = False
        self.assertTrue(pfc.give_part(Part()))


if __name__ == '__main__':
    unittest.main()
