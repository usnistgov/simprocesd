from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, EventType, System
from ....model.factory_floor import Part, Machine, MachineStatusTracker


class MachineTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 1
        self.upstream = [MagicMock(spec = Machine), MagicMock(spec = Machine)]

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
        status_tracker = MachineStatusTracker()
        machine = Machine('mb', self.upstream, 2, status_tracker, 15)
        self.assertIn(machine, self.sys._assets)
        machine.initialize(self.env)
        self.assertEqual(machine.name, 'mb')
        self.assertEqual(machine.value, 15)
        self.assertEqual(machine.upstream, self.upstream)
        self.assertEqual(machine.status_tracker, status_tracker)

    def test_re_initialize(self):
        status_tracker = MachineStatusTracker()
        machine = Machine('mb', self.upstream, 2, status_tracker, 15)
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
        self.assertEqual(machine.status_tracker, status_tracker)

    def test_is_operational(self):
        mst_mock = MagicMock(spec = MachineStatusTracker)
        machine = Machine(status_tracker = mst_mock)
        machine.initialize(self.env)

        mst_mock.is_operational.return_value = True
        self.assertTrue(machine.is_operational())

        mst_mock.is_operational.return_value = False
        self.assertFalse(machine.is_operational())

        machine.shutdown()
        self.assertFalse(machine.is_operational())

        mst_mock.is_operational.return_value = True
        self.assertFalse(machine.is_operational())

    def test_shutdown(self):
        machine = Machine()
        machine.initialize(self.env)
        machine.shutdown()

        self.env.pause_matching_events.assert_called_with(asset_id = machine.id)
        self.assertFalse(machine.is_operational())

    def test_restore(self):
        mst_mock = MagicMock(spec = MachineStatusTracker)
        machine = Machine(upstream = self.upstream, status_tracker = mst_mock)
        machine.initialize(self.env)
        machine.shutdown()
        # Attempt to restore when status tracker is not operational.
        mst_mock.is_operational.return_value = False
        machine.restore_functionality()
        self.assertFalse(machine.is_operational())
        self.env.unpause_matching_events.assert_not_called()
        for u in self.upstream:
            u.space_available_downstream.assert_not_called()

        mst_mock.is_operational.return_value = True
        machine.restore_functionality()
        self.assertTrue(machine.is_operational())
        self.env.unpause_matching_events.assert_called_with(asset_id = machine.id)
        for u in self.upstream:
            u.space_available_downstream.assert_called_once()

    def test_restore_with_part(self):
        machine = Machine()
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
        self.assert_last_scheduled_event(self.env.now, machine.id, machine._pass_part_downstream,
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
        machine = Machine()
        shutdown_cb = MagicMock()
        machine.add_shutdown_callback(shutdown_cb)
        machine.initialize(self.env)
        part = Part()
        machine.give_part(part)

        shutdown_cb.assert_not_called()
        machine._fail()
        shutdown_cb.assert_called_once_with(machine, True, part)

    def test_restore_callback(self):
        machine = Machine()
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

        self.assert_last_scheduled_event(10, machine.id, machine._fail, EventType.FAIL)
        machine._fail()
        self.env.cancel_matching_events.assert_called_with(asset_id = machine.id)

    def test_failure_with_parts(self):
        part1, part2 = Part(), Part()
        machine = Machine()
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
        self.assert_last_scheduled_event(self.env.now + 3, machine.id,
                machine._finish_processing_part, EventType.FINISH_PROCESSING)

    def test_process_part(self):
        machine = Machine(cycle_time = 0, upstream = self.upstream)
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
        self.assert_last_scheduled_event(self.env.now, machine.id, machine._pass_part_downstream,
                                    EventType.PASS_PART)

    def test_process_part_when_not_operational(self):
        mst_mock = MagicMock(spec = MachineStatusTracker)
        machine = Machine(status_tracker = mst_mock)
        machine.initialize(self.env)
        machine.give_part(Part())
        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        mst_mock.is_operational.return_value = False

        machine._finish_processing_part()
        # No new events have been scheduled and part is not processed.
        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        self.assertEqual(machine._output, None)

    def test_changing_cycle_time(self):
        machine = Machine(cycle_time = 5, upstream = self.upstream)
        machine.initialize(self.env)
        machine.give_part(Part())
        self.assert_last_scheduled_event(self.env.now + 5, machine.id,
                machine._finish_processing_part, EventType.FINISH_PROCESSING)
        machine.cycle_time = 12
        self.env.now += 5
        machine._finish_processing_part()
        machine._output = None  # Simulate passing part downstream.

        machine.give_part(Part())
        self.assert_last_scheduled_event(self.env.now + 12, machine.id,
                machine._finish_processing_part, EventType.FINISH_PROCESSING)


if __name__ == '__main__':
    unittest.main()
