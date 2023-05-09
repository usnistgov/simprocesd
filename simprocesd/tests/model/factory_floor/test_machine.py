from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, EventType, System, ResourceManager
from ....model.factory_floor import Part, Machine
from ....model.resource_manager import ReservedResources


class MachineTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.rm = MagicMock(spec = ResourceManager)
        self.rm._init_count = 1
        self.env = MagicMock(spec = Environment)
        self.env.now = 1
        self.env.resource_manager = self.rm
        self.rm._env = self.env
        self.upstream = [MagicMock(spec = Machine), MagicMock(spec = Machine)]

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
        machine = Machine('mb', self.upstream, 2, 15)
        self.assertIn(machine, self.sys._assets)
        machine.initialize(self.env)
        self.assertEqual(machine.name, 'mb')
        self.assertEqual(machine.value, 15)
        self.assertEqual(machine.upstream, self.upstream)

    def test_re_initialize(self):
        machine = Machine('mb', self.upstream, 2, 15)
        machine.initialize(self.env)

        part = Part()
        machine.give_part(part)
        machine.add_value('', 20)
        self.assertEqual(machine._part, part)
        self.assertEqual(machine.value, 15 + 20)

        machine.initialize(self.env)
        self.assertEqual(machine._part, None)
        self.assertEqual(machine.value, 15)
        self.assertEqual(machine.upstream, self.upstream)

    def test_is_operational(self):
        machine = Machine()
        machine.initialize(self.env)

        self.assertTrue(machine.is_operational())
        machine.shutdown()
        self.assertFalse(machine.is_operational())

    def test_shutdown(self):
        machine = Machine()
        machine.initialize(self.env)
        machine.shutdown()

        self.env.pause_matching_events.assert_called_once_with(asset_id = machine.id)
        self.assertFalse(machine.is_operational())
        # Shutdown call should do nothing if Machine is already
        # shutdown.
        machine.shutdown()
        self.env.pause_matching_events.assert_called_once()

    def test_restore(self):
        machine = Machine(upstream = self.upstream)
        machine.initialize(self.env)
        machine.shutdown()

        machine.restore_functionality()
        self.assertTrue(machine.is_operational())
        self.env.unpause_matching_events.assert_called_with(asset_id = machine.id)
        for u in self.upstream:
            u.space_available_downstream.assert_called_once()

    def test_restore_with_part(self):
        machine = Machine(cycle_time = 1)
        machine.initialize(self.env)
        machine.give_part(Part())
        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        machine._finish_processing_part()
        self.assertEqual(len(self.env.schedule_event.call_args_list), 2)
        machine.shutdown()
        machine.restore_functionality()
        # give_part schedules _finish_processing_part,
        # finish_processing_part schedules _pass_part_downstream,
        # shutdown+restore should schedule _pass_part_downstream again.
        self.assertEqual(len(self.env.schedule_event.call_args_list), 3)
        self.assert_scheduled_event(-1, self.env.now, machine.id, machine._pass_part_downstream,
                                    EventType.PASS_PART)

    def test_shutdown_callback(self):
        machine = Machine()
        shutdown_cb = MagicMock()
        machine.add_shutdown_callback(shutdown_cb)
        machine.initialize(self.env)
        part = Part()
        machine.give_part(part)

        shutdown_cb.assert_not_called()
        machine.shutdown()
        shutdown_cb.assert_called_once_with(machine, False, None)

    def test_shutdown_callback_on_fail(self):
        machine = Machine(cycle_time = 1)
        shutdown_cb = MagicMock()
        machine.add_shutdown_callback(shutdown_cb)
        machine.initialize(self.env)
        part = Part()
        machine.give_part(part)

        shutdown_cb.assert_not_called()
        machine._fail()
        shutdown_cb.assert_called_once_with(machine, True, part)

    def test_restore_callback(self):
        machine = Machine(cycle_time = 1)
        restore_cb = MagicMock()
        machine.add_restored_callback(restore_cb)
        machine.initialize(self.env)
        machine.shutdown()

        restore_cb.assert_not_called()
        machine.restore_functionality()
        restore_cb.assert_called_once_with(machine)

    def test_schedule_failure(self):
        machine = Machine(upstream = self.upstream)
        machine.initialize(self.env)
        machine.schedule_failure(10, 'fail_machine')

        self.assert_scheduled_event(-1, 10, machine.id, machine._fail, EventType.FAIL)
        machine._fail()
        self.env.cancel_matching_events.assert_called_with(asset_id = machine.id)

    def test_failure_with_parts(self):
        part1, part2 = Part(), Part()
        machine = Machine(cycle_time = 1)
        machine.initialize(self.env)
        machine.give_part(part1)

        machine._fail()
        self.assertEqual(machine._part, None)

        machine.restore_functionality()
        machine.give_part(part2)
        machine._finish_processing_part()
        machine._fail()
        self.assertEqual(machine._output, part2)

    def test_receive_part(self):
        machine = Machine(cycle_time = 3)
        received_part_cb = MagicMock()
        machine.add_receive_part_callback(received_part_cb)
        machine.initialize(self.env)
        part = Part()

        received_part_cb.assert_not_called()
        machine.give_part(part)
        received_part_cb.assert_called_once_with(machine, part)
        self.env.add_datapoint.assert_called_once()
        self.assert_scheduled_event(-1, self.env.now + 3, machine.id,
                machine._finish_processing_part, EventType.FINISH_PROCESSING)

    def test_receive_part_callback(self):
        machine = Machine(cycle_time = 3)

        def cb(m, p):
            m.cycle_time += 1

        machine.add_receive_part_callback(cb)
        machine.initialize(self.env)

        machine.give_part(Part())
        self.assert_scheduled_event(-1, self.env.now + 3 + 1, machine.id,
                machine._finish_processing_part, EventType.FINISH_PROCESSING)
        machine._finish_processing_part()
        machine._output = None

        machine.give_part(Part())
        self.assert_scheduled_event(-1, self.env.now + 3 + 1 + 1, machine.id,
                machine._finish_processing_part, EventType.FINISH_PROCESSING)

    def test_process_part(self):
        machine = Machine(cycle_time = 1, upstream = self.upstream)
        finished_processing_cb = MagicMock()
        machine.add_finish_processing_callback(finished_processing_cb)
        machine.initialize(self.env)
        part = Part()
        machine.give_part(part)
        self.assertEqual(len(self.env.add_datapoint.call_args_list), 1)

        finished_processing_cb.assert_not_called()
        machine._finish_processing_part()
        finished_processing_cb.assert_called_once_with(machine, part)
        self.assertEqual(len(self.env.add_datapoint.call_args_list), 2)
        self.assert_scheduled_event(-1, self.env.now, machine.id, machine._pass_part_downstream,
                                    EventType.PASS_PART)

    def test_process_part_when_not_operational(self):
        machine = Machine()
        machine.initialize(self.env)
        machine.give_part(Part())
        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        machine.shutdown()

        self.assertRaises(AssertionError, lambda: machine._finish_processing_part())

    def test_changing_cycle_time(self):
        machine = Machine(cycle_time = 5, upstream = self.upstream)
        machine.initialize(self.env)
        machine.give_part(Part())
        self.assert_scheduled_event(-1, self.env.now + 5, machine.id,
                machine._finish_processing_part, EventType.FINISH_PROCESSING)
        machine.cycle_time = 12
        self.env.now += 5
        machine._finish_processing_part()
        machine._output = None  # Simulate passing part downstream.

        machine.give_part(Part())
        self.assert_scheduled_event(-1, self.env.now + 12, machine.id,
                machine._finish_processing_part, EventType.FINISH_PROCESSING)

    def test_uptime_tracking(self):
        machine = Machine()
        machine.initialize(self.env)
        self.assertEqual(machine.uptime, 0)

        self.env.now += 5
        self.assertEqual(machine.uptime, 5)
        self.env.now += 7
        self.assertEqual(machine.uptime, 12)

        machine.shutdown()
        self.env.now += 4
        self.assertEqual(machine.uptime, 12)
        self.env.now += 15
        machine.restore_functionality()
        self.assertEqual(machine.uptime, 12)
        self.env.now += 12
        self.assertEqual(machine.uptime, 24)

    def test_utilization_tracking(self):
        machine = Machine(cycle_time = 1)
        machine.initialize(self.env)
        self.assertEqual(machine.utilization_time, 0)

        self.env.now += 3
        machine.give_part(Part())
        self.assertEqual(machine.utilization_time, 0)
        self.env.now += 4
        self.assertEqual(machine.utilization_time, 4)
        self.env.now += 5
        self.assertEqual(machine.utilization_time, 9)
        machine.shutdown()
        self.assertEqual(machine.utilization_time, 9)
        self.env.now += 6
        machine.restore_functionality()
        self.assertEqual(machine.utilization_time, 9)
        self.env.now += 7
        self.assertEqual(machine.utilization_time, 16)
        machine._finish_processing_part()
        self.env.now += 8
        self.assertEqual(machine.utilization_time, 16)

    def test_utilization_tracking_with_failure(self):
        machine = Machine(cycle_time = 1)
        machine.initialize(self.env)

        machine.give_part(Part())
        self.env.now += 3
        self.assertEqual(machine.utilization_time, 3)
        machine._fail()
        self.env.now += 4
        self.assertEqual(machine.utilization_time, 3)
        machine.restore_functionality()
        self.env.now += 5
        self.assertEqual(machine.utilization_time, 3)

        machine.give_part(Part())
        self.env.now += 6
        self.assertEqual(machine.utilization_time, 9)

    def test_resource_request(self):
        rr = MagicMock(spec = ReservedResources)
        rr.reserved_resources.return_value = {'tool': 1}
        self.rm.reserve_resources.return_value = rr
        machine = Machine(cycle_time = 1, resources_for_processing = {'tool': 1})

        machine.initialize(self.env)
        part = Part()

        self.assertTrue(machine.give_part(part))
        self.assertEqual(machine._part, part)
        self.assertEqual(machine._reserved_resources, rr)
        self.rm.reserve_resources.assert_called_once_with({'tool': 1})
        self.assert_scheduled_event(-1, self.env.now + 1, machine.id,
                machine._finish_processing_part, EventType.FINISH_PROCESSING)
        rr.release.assert_not_called()

        machine._finish_processing_part()
        self.rm.reserve_resources.assert_called_once_with({'tool': 1})
        self.assert_scheduled_event(-2, self.env.now, machine.id,
                machine._release_resources_if_idle, EventType.RELEASE_RESERVED_RESOURCES)

        machine._release_resources_if_idle()
        rr.release.assert_called_once()

    def test_resource_request_fail(self):
        # Setup a failed attempt at reserving resources.
        self.rm.reserve_resources.return_value = None
        machine = Machine(cycle_time = 1, upstream = self.upstream, resources_for_processing = {'tool': 1})

        machine.initialize(self.env)
        part = Part()
        self.rm.reserve_resources_with_callback.assert_not_called()

        self.assertFalse(machine.give_part(part))
        self.assertEqual(machine._part, None)
        self.rm.reserve_resources_with_callback.assert_called_once_with(
                {'tool': 1}, machine._reserve_resource_callback)
        # Test that multiple callbacks aren't added.
        self.assertFalse(machine.give_part(part))
        self.rm.reserve_resources_with_callback.assert_called_once()

        self.upstream[0].space_available_downstream.assert_not_called()
        machine._reserve_resource_callback({'tool': 1})
        self.upstream[0].space_available_downstream.assert_called_once()

    def test_resource_request_with_failure(self):
        rr = MagicMock(spec = ReservedResources)
        self.rm.reserve_resources.return_value = rr
        machine = Machine(cycle_time = 1, resources_for_processing = {'tool': 1})

        machine.initialize(self.env)
        part = Part()

        self.assertTrue(machine.give_part(part))
        rr.release.assert_not_called()

        machine.shutdown()
        machine.restore_functionality()
        rr.release.assert_not_called()

        machine._fail()
        rr.release.assert_called_once()

    def test_process_part_instant(self):
        machine = Machine(cycle_time = 0)
        machine.initialize(self.env)
        part = Part()
        machine.give_part(part)
        self.assertEqual(len(self.env.add_datapoint.call_args_list), 2)
        self.assert_scheduled_event(-1, self.env.now, machine.id, machine._pass_part_downstream,
                                    EventType.PASS_PART)


if __name__ == '__main__':
    unittest.main()
