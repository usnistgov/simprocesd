from unittest import TestCase
import unittest
from unittest.mock import MagicMock, call

from ... import mock_wrap
from ....model import Environment, EventType, System
from ....model.factory_floor import Part
from simprocesd.model.factory_floor.part_handler import PartHandler


class PartHandlerTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.upstream = [PartHandler(), PartHandler()]
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

    def add_downstream(self, target, give_part_return = True, waiting_for_part_start_time = 0):
        downstream = MagicMock(spec = PartHandler)
        downstream.give_part.return_value = give_part_return
        downstream.waiting_for_part_start_time = waiting_for_part_start_time
        if target != None:
            target._add_downstream(downstream)
        return downstream

    def test_initialize(self):
        ph = PartHandler('mb', self.upstream, 5, 10)
        self.assertIn(ph, self.sys._assets)
        ph.initialize(self.env)
        self.assertEqual(ph.name, 'mb')
        self.assertEqual(ph.cycle_time, 5)
        self.assertEqual(ph.value, 10)
        self.assertEqual(ph.upstream, self.upstream)
        self.assertEqual(ph.downstream, [])
        self.assertTrue(ph.is_operational)
        self.assertEqual(ph.waiting_for_part_start_time, 0)
        self.assertEqual(ph.block_input, False)

    def test_set_upstream(self):
        ph = PartHandler()
        ph.set_upstream(self.upstream)
        self.assertEqual(ph.waiting_for_part_start_time, None)
        ph.initialize(self.env)
        self.assertEqual(ph.waiting_for_part_start_time, self.env.now)

        self.env.now += 5
        new_upstream = [PartHandler()]
        ph.set_upstream(new_upstream)
        self.assertEqual(ph.waiting_for_part_start_time, self.env.now)

        self.env.now += 10
        ph._set_waiting_for_part(False)
        self.assertEqual(ph.waiting_for_part_start_time, None)
        ph.set_upstream(self.upstream)
        self.assertEqual(ph.waiting_for_part_start_time, None)

    def test_notify_upstream_of_available_space(self):
        mocked_upstream = mock_wrap(self.upstream)
        ph = PartHandler(upstream = mocked_upstream)
        ph.initialize(self.env)

        self.env.now += 5
        ph._set_waiting_for_part(False)
        ph.notify_upstream_of_available_space()
        for u in mocked_upstream:
            u.space_available_downstream.assert_called_once()
        self.assertEqual(ph.waiting_for_part_start_time, self.env.now)

        ph._set_waiting_for_part(False)

    def test_give_part(self):
        part1, part2 = Part(), Part()
        ph = PartHandler(upstream = self.upstream)
        ph.initialize(self.env)

        self.assertEqual(ph.waiting_for_part_start_time, 0)
        # PartHandler can only hold 1 part at a time.
        self.assertTrue(ph.give_part(part1))
        self.assertEqual(part1.routing_history, [ph])
        self.assertEqual(ph.waiting_for_part_start_time, None)
        self.assertFalse(ph.give_part(part2))
        self.assertEqual(part2.routing_history, [])

    def test_receive_part_callback(self):
        part = Part()
        ph = PartHandler(upstream = self.upstream)
        ph.initialize(self.env)
        received_part_cb = MagicMock()
        ph.add_receive_part_callback(received_part_cb)

        received_part_cb.assert_not_called()
        ph.give_part(part)
        received_part_cb.assert_called_once_with(ph, part)

    def test_update_cycle_time_in_callback(self):
        ph = PartHandler(cycle_time = 3)

        def cb(partHandler, part):
            partHandler.cycle_time += 1

        ph.add_receive_part_callback(cb)
        ph.initialize(self.env)

        ph.give_part(Part())
        self.assert_last_scheduled_event(self.env.now + 3 + 1, ph.id,
                ph._finish_cycle, EventType.FINISH_PROCESSING)
        ph._finish_cycle()
        ph._output = None
        ph.give_part(Part())
        self.assert_last_scheduled_event(self.env.now + 3 + 1 + 1, ph.id,
                ph._finish_cycle, EventType.FINISH_PROCESSING)

    def test_give_part_when_not_operational(self):
        part = Part()
        ph = PartHandler(upstream = self.upstream)
        ph.initialize(self.env)

        ph.is_operational = lambda: False
        self.assertFalse(ph.give_part(part))
        self.assertEqual(part.routing_history, [])

    def test_space_available_downstream(self):
        ph = PartHandler(upstream = self.upstream)
        ph.initialize(self.env)

        ph.space_available_downstream()
        self.env.schedule_event.assert_not_called()

        # Because cycle time is 0 _finish_cycle is called immediately.
        ph.give_part(Part())
        self.assert_last_scheduled_event(self.env.now, ph.id, ph._pass_part_downstream,
                                    EventType.PASS_PART)
        # Part will not be passed because downstream was not defined.
        ph._pass_part_downstream()
        self.assertEqual(ph.waiting_for_part_start_time, None)

        self.env.now += 5
        ph.space_available_downstream()
        self.assert_last_scheduled_event(self.env.now, ph.id, ph._pass_part_downstream,
                                    EventType.PASS_PART)

    def test_full_cycle(self):
        part = Part()
        mocked_upstream = mock_wrap(self.upstream)
        ph = PartHandler(upstream = mocked_upstream, cycle_time = 3)
        ph.initialize(self.env)
        downstream = self.add_downstream(ph, True, 0)

        ph._pass_part_downstream()
        for u in mocked_upstream:
            u.space_available_downstream.assert_not_called()

        self.env.now = 10
        self.env.schedule_event.assert_not_called()
        ph.give_part(part)
        self.assert_last_scheduled_event(self.env.now + 3, ph.id, ph._finish_cycle,
                                    EventType.FINISH_PROCESSING)

        self.env.now += 3
        ph._finish_cycle()
        self.assert_last_scheduled_event(self.env.now, ph.id, ph._pass_part_downstream,
                                    EventType.PASS_PART)

        ph._pass_part_downstream()
        downstream.give_part.assert_called_once_with(part)
        for u in mocked_upstream:
            u.space_available_downstream.assert_called_once()

        downstream.give_part.reset_mock()
        ph._pass_part_downstream()
        # Check that a part does not get passed a second time.
        downstream.give_part.assert_not_called()

    def test_pass_part_downstream_when_one_downstream_blocked(self):
        part = Part()
        mocked_upstream = mock_wrap(self.upstream)
        ph = PartHandler(upstream = mocked_upstream, cycle_time = 1)
        ph.initialize(self.env)

        downstream1 = self.add_downstream(ph, False, 0)
        # No valid downstream to pass part to.
        ph.give_part(part)
        ph._finish_cycle()
        ph._pass_part_downstream()
        downstream1.give_part.assert_called_once_with(part)
        # New downstream available that can accept the part.
        downstream2 = self.add_downstream(ph, True, 0)
        ph._pass_part_downstream()
        calls = [call(part), call(part)]
        downstream1.give_part.assert_has_calls(calls)
        downstream2.give_part.assert_called_once_with(part)

    def test_pass_part_downstream_order(self):
        ph = PartHandler()
        ph.initialize(self.env)
        downstreams = []
        for i in range(3):
            downstreams.append(self.add_downstream(ph, True, i))
            downstreams[-1].give_part.return_value = True
            downstreams[-1].waiting_for_part_start_time = i

        ph.give_part(Part())
        ph._pass_part_downstream()
        # Waiting start times: 0, 1, 2
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 1)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 0)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 0)

        downstreams[0].waiting_for_part_start_time = 4
        downstreams[1].waiting_for_part_start_time = 6
        ph.give_part(Part())
        ph._pass_part_downstream()
        # Waiting start times: 4, 6, 2
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 1)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 0)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 1)

        downstreams[2].waiting_for_part_start_time = 10
        ph.give_part(Part())
        ph._pass_part_downstream()
        # Waiting start times: 4, 6, 10
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 2)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 0)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 1)
        # None means PartHandler is not marked as waiting for parts.
        downstreams[0].waiting_for_part_start_time = None
        ph.give_part(Part())
        ph._pass_part_downstream()
        # Waiting start times: --, 6, 10
        self.assertEqual(len(downstreams[0].give_part.call_args_list), 2)
        self.assertEqual(len(downstreams[1].give_part.call_args_list), 1)
        self.assertEqual(len(downstreams[2].give_part.call_args_list), 1)

    def test_changing_cycle_time(self):
        ph = PartHandler(cycle_time = 5, upstream = self.upstream)
        ph.initialize(self.env)

        ph.give_part(Part())
        self.assert_last_scheduled_event(self.env.now + 5, ph.id,
                ph._finish_cycle, EventType.FINISH_PROCESSING)
        self.env.now += 5
        ph._finish_cycle()
        ph._output = None  # Simulate passing part downstream.

        ph.cycle_time = 12
        ph.give_part(Part())
        self.assert_last_scheduled_event(self.env.now + 12, ph.id,
                ph._finish_cycle, EventType.FINISH_PROCESSING)

    def test_offset_next_cycle_time(self):
        mocked_upstream = mock_wrap(self.upstream)
        ph = PartHandler(upstream = mocked_upstream, cycle_time = 0)
        ph.initialize(self.env)

        ph.offset_next_cycle_time(5)
        ph.give_part(Part())
        self.assert_last_scheduled_event(self.env.now + 5, ph.id,
                ph._finish_cycle, EventType.FINISH_PROCESSING)

        self.env.now += 15
        ph._finish_cycle()
        ph._output = None
        ph.offset_next_cycle_time(7)
        ph.offset_next_cycle_time(-3)
        ph.offset_next_cycle_time(4)
        ph.give_part(Part())
        self.assert_last_scheduled_event(self.env.now + 8, ph.id,
                ph._finish_cycle, EventType.FINISH_PROCESSING)

    def test_negative_offset_next_cycle_time_(self):
        ph = PartHandler(cycle_time = 10)
        ph.initialize(self.env)

        ph.offset_next_cycle_time(-6)
        ph.give_part(Part())
        self.assertEqual(ph._output, None)
        self.assert_last_scheduled_event(self.env.now + 4, ph.id,
                ph._finish_cycle, EventType.FINISH_PROCESSING)

        self.env.now += 4
        ph._finish_cycle()
        ph._output = None
        ph.offset_next_cycle_time(-20)
        ph.give_part(Part())
        self.assertNotEqual(ph._output, None)

    def test_process_part_instant(self):
        ph = PartHandler(cycle_time = 0)
        ph.initialize(self.env)
        part = Part()
        ph.give_part(part)
        # _finish_cycle event is skipped
        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        self.assert_last_scheduled_event(self.env.now, ph.id, ph._pass_part_downstream,
                                    EventType.PASS_PART)


if __name__ == '__main__':
    unittest.main()
