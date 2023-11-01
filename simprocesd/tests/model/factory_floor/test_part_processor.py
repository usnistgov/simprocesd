from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, EventType, System, ResourceManager
from ....model.factory_floor import Part, PartProcessor
from ....model.resource_manager import ReservedResources


class ppTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.rm = MagicMock(spec = ResourceManager)
        self.env = MagicMock(spec = Environment)
        self.env.now = 0
        self.env.resource_manager = self.rm
        self.rm._env = self.env
        self.upstream = [MagicMock(spec = PartProcessor), MagicMock(spec = PartProcessor)]

    def assert_scheduled_event(self, event_index, time, id_, action, event_type, message = None):
        args, kwargs = self.env.schedule_event.call_args_list[event_index]
        self.assertEqual(args[0], time)
        self.assertEqual(args[1], id_)
        self.assertEqual(args[2], action)
        self.assertEqual(args[3], event_type)
        self.assertIsInstance(args[4], str)
        if message != None:
            self.assertEqual(args[4], message)

    def test_initialize(self):
        pp = PartProcessor('mb', self.upstream, 2, 15)
        self.assertIn(pp, self.sys._assets)
        pp.initialize(self.env)
        self.assertEqual(pp.name, 'mb')
        self.assertEqual(pp.value, 15)
        self.assertEqual(pp.upstream, self.upstream)
        self.assertEqual(pp.cycle_time, 2)
        self.assertTrue(pp.is_operational)
        self.assertEqual(pp.waiting_for_part_start_time, 0)
        self.assertEqual(pp.block_input, False)

    def test_is_operational(self):
        pp = PartProcessor()
        pp.initialize(self.env)

        self.assertTrue(pp.is_operational())
        pp.shutdown()
        self.assertFalse(pp.is_operational())
        pp.restore_functionality()
        self.assertTrue(pp.is_operational())

    def test_shutdown(self):
        pp = PartProcessor()
        pp.initialize(self.env)

        self.env.pause_matching_events.assert_not_called()
        pp.shutdown()
        self.env.pause_matching_events.assert_called_once_with(asset_id = pp.id)
        self.env.reset_mock()
        # Shutdown call should do nothing if PartProcessor is already
        # shutdown.
        pp.shutdown()
        self.env.pause_matching_events.assert_not_called()

    def test_restore(self):
        pp = PartProcessor(upstream = self.upstream)
        pp.initialize(self.env)

        pp.shutdown()
        self.env.unpause_matching_events.assert_not_called()
        pp.restore_functionality()
        self.env.unpause_matching_events.assert_called_with(asset_id = pp.id)
        for u in self.upstream:
            u.space_available_downstream.assert_called_once()

    def test_restore_with_part(self):
        pp = PartProcessor(cycle_time = 1)
        pp.initialize(self.env)

        pp.give_part(Part())
        pp._finish_cycle()
        pp.shutdown()
        self.env.reset_mock()
        pp.restore_functionality()
        # give_part schedules _finish_cycle,
        # finish_processing_part schedules _pass_part_downstream,
        # shutdown+restore should schedule _pass_part_downstream again.
        self.env.schedule_event.assert_called_once()
        self.assert_scheduled_event(-1, self.env.now, pp.id, pp._pass_part_downstream,
                                    EventType.PASS_PART)
        for u in self.upstream:
            u.space_available_downstream.assert_not_called()

    def test_shutdown_callback(self):
        pp = PartProcessor()
        shutdown_cb = MagicMock()
        pp.add_shutdown_callback(shutdown_cb)
        pp.initialize(self.env)
        part = Part()
        pp.give_part(part)

        shutdown_cb.assert_not_called()
        pp.shutdown()
        shutdown_cb.assert_called_once_with(pp, False, None)

    def test_shutdown_callback_on_fail(self):
        pp = PartProcessor(cycle_time = 1)
        shutdown_cb = MagicMock()
        pp.add_shutdown_callback(shutdown_cb)
        pp.initialize(self.env)
        part = Part()
        pp.give_part(part)

        shutdown_cb.assert_not_called()
        pp._fail()
        shutdown_cb.assert_called_once_with(pp, True, part)

        shutdown_cb.reset_mock()
        pp.restore_functionality()
        pp._fail()
        shutdown_cb.assert_called_once_with(pp, True, None)

    def test_restore_callback(self):
        pp = PartProcessor(cycle_time = 1)
        restore_cb = MagicMock()
        pp.add_restored_callback(restore_cb)
        pp.initialize(self.env)
        pp.shutdown()

        restore_cb.assert_not_called()
        pp.restore_functionality()
        restore_cb.assert_called_once_with(pp)

    def test_schedule_failure(self):
        pp = PartProcessor(upstream = self.upstream)
        pp.initialize(self.env)
        msg = 'fail_PartProcessor'
        pp.schedule_failure(10, msg)

        self.assert_scheduled_event(-1, 10, pp.id, pp._fail, EventType.FAIL, msg)
        pp._fail()
        self.env.cancel_matching_events.assert_called_with(asset_id = pp.id)

    def test_failure_with_parts(self):
        part1, part2 = Part(), Part()
        pp = PartProcessor(cycle_time = 1)
        pp.initialize(self.env)
        pp.give_part(part1)

        pp._fail()
        self.assertEqual(pp._part, None)

        pp.restore_functionality()
        pp.give_part(part2)
        pp._finish_cycle()
        pp._fail()
        self.assertEqual(pp._output, part2)

    def test_receive_part(self):
        pp = PartProcessor(cycle_time = 3)
        received_part_cb = MagicMock()
        pp.add_receive_part_callback(received_part_cb)
        pp.initialize(self.env)
        part = Part('p', 10, 0.5)

        received_part_cb.assert_not_called()
        pp.give_part(part)
        received_part_cb.assert_called_once_with(pp, part)
        self.env.add_datapoint.assert_called_once_with('received_part', pp.name,
                (self.env.now, part.id, part.quality, part.value))
        self.assert_scheduled_event(-1, self.env.now + 3, pp.id,
                pp._finish_cycle, EventType.FINISH_PROCESSING)

    def test_process_part(self):
        pp = PartProcessor(cycle_time = 1, upstream = self.upstream)
        finished_processing_cb = MagicMock()
        pp.add_finish_processing_callback(finished_processing_cb)
        pp.initialize(self.env)
        part = Part()

        pp.give_part(part)
        finished_processing_cb.assert_not_called()
        self.env.reset_mock()
        pp._finish_cycle()
        finished_processing_cb.assert_called_once_with(pp, part)
        self.assert_scheduled_event(-1, self.env.now, pp.id, pp._pass_part_downstream,
                                    EventType.PASS_PART)

    def test_process_part_when_not_operational(self):
        pp = PartProcessor()
        pp.initialize(self.env)
        pp.give_part(Part())
        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        pp.shutdown()

        self.assertRaises(AssertionError, lambda: pp._finish_cycle())

    def test_uptime_tracking(self):
        pp = PartProcessor()
        pp.initialize(self.env)
        self.assertEqual(pp.uptime, 0)

        self.env.now += 5
        self.assertEqual(pp.uptime, 5)
        self.env.now += 7
        self.assertEqual(pp.uptime, 12)

        pp.shutdown()
        self.env.now += 4
        self.assertEqual(pp.uptime, 12)
        self.env.now += 15
        pp.restore_functionality()
        self.assertEqual(pp.uptime, 12)
        self.env.now += 12
        self.assertEqual(pp.uptime, 24)

    def test_utilization_tracking(self):
        pp = PartProcessor(cycle_time = 1)
        pp.initialize(self.env)
        self.assertEqual(pp.utilization_time, 0)

        self.env.now += 3
        pp.give_part(Part())
        self.assertEqual(pp.utilization_time, 0)
        self.env.now += 4
        self.assertEqual(pp.utilization_time, 4)
        self.env.now += 5
        self.assertEqual(pp.utilization_time, 9)
        pp.shutdown()
        self.env.now += 6
        self.assertEqual(pp.utilization_time, 9)
        self.env.now += 7
        pp.restore_functionality()
        self.assertEqual(pp.utilization_time, 9)
        self.env.now += 8
        self.assertEqual(pp.utilization_time, 17)
        pp._finish_cycle()
        self.env.now += 8
        self.assertEqual(pp.utilization_time, 17)

    def test_utilization_tracking_with_failure(self):
        pp = PartProcessor(cycle_time = 1)
        pp.initialize(self.env)

        pp.give_part(Part())
        self.env.now += 3
        self.assertEqual(pp.utilization_time, 3)
        pp._fail()
        self.env.now += 4
        self.assertEqual(pp.utilization_time, 3)
        pp.restore_functionality()
        self.env.now += 5
        self.assertEqual(pp.utilization_time, 3)

        pp.give_part(Part())
        self.env.now += 6
        self.assertEqual(pp.utilization_time, 9)

    def test_resource_request(self):
        rr = MagicMock(spec = ReservedResources)
        rr.reserved_resources.return_value = {'tool': 1}
        self.rm.reserve_resources.return_value = rr
        pp = PartProcessor(cycle_time = 1, resources_for_processing = {'tool': 1})
        pp.initialize(self.env)
        part = Part()

        self.rm.reserve_resources.assert_not_called()
        self.assertTrue(pp.give_part(part))
        self.assertEqual(pp._reserved_resources, rr)
        self.rm.reserve_resources.assert_called_once_with({'tool': 1})
        self.assert_scheduled_event(-1, self.env.now + 1, pp.id,
                pp._finish_cycle, EventType.FINISH_PROCESSING)
        rr.release.assert_not_called()

        self.rm.reset_mock()
        pp._finish_cycle()
        self.rm.reserve_resources.assert_not_called()
        self.assert_scheduled_event(-1, self.env.now, pp.id,
                pp._release_resources_if_idle, EventType.RELEASE_RESERVED_RESOURCES)

        pp._release_resources_if_idle()
        rr.release.assert_called_once_with()

    def test_resource_request_sequential_parts(self):
        rr = MagicMock(spec = ReservedResources)
        rr.reserved_resources.return_value = {'tool': 1}
        self.rm.reserve_resources.return_value = rr
        pp = PartProcessor(cycle_time = 1, resources_for_processing = {'tool': 1})
        pp.initialize(self.env)

        self.assertTrue(pp.give_part(Part()))
        pp._finish_cycle()
        pp._output = None
        self.assertTrue(pp.give_part(Part()))
        pp._release_resources_if_idle()
        # Not idle because received new part.
        rr.release.assert_not_called()
        self.rm.reserve_resources.assert_called_once()

    def test_resource_request_fail(self):
        # Setup a failed attempt at reserving resources.
        self.rm.reserve_resources.return_value = None
        pp = PartProcessor(cycle_time = 1, upstream = self.upstream, resources_for_processing = {'tool': 1})
        pp.initialize(self.env)
        part = Part()

        self.rm.reserve_resources_with_callback.assert_not_called()
        self.assertFalse(pp.give_part(part))
        self.assertEqual(pp._part, None)
        self.rm.reserve_resources_with_callback.assert_called_once_with(
                {'tool': 1}, pp._reserve_resource_callback)
        # Test that multiple callbacks aren't added.
        self.rm.reset_mock()
        self.assertFalse(pp.give_part(part))
        self.rm.reserve_resources.assert_called_once()
        self.rm.reserve_resources_with_callback.assert_not_called()
        self.upstream[0].space_available_downstream.assert_not_called()

        pp._reserve_resource_callback(self.rm, {'tool': 1})
        # Notify upstream but do not reserve resources.
        self.rm.reserve_resources.assert_called_once()
        self.rm.reserve_resources_with_callback.assert_not_called()
        self.upstream[0].space_available_downstream.assert_called_once()

    def test_resource_request_with_failure(self):
        rr = MagicMock(spec = ReservedResources)
        self.rm.reserve_resources.return_value = rr
        pp = PartProcessor(cycle_time = 1, resources_for_processing = {'tool': 1})
        pp.initialize(self.env)

        self.assertTrue(pp.give_part(Part()))
        rr.release.assert_not_called()

        pp.shutdown()
        pp.restore_functionality()
        rr.release.assert_not_called()

        pp._fail()
        rr.release.assert_called_once()


if __name__ == '__main__':
    unittest.main()
