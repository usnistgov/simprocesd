from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, EventType, System
from ....model.factory_floor import Machine, DeviceSchedule


class DeviceScheduleTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 0
        self.devices = [MagicMock(spec = Machine), MagicMock(spec = Machine)]

    def assert_scheduled_event(self, event_index, time, id_, action, event_type):
        args, kwargs = self.env.schedule_event.call_args_list[event_index]
        self.assertEqual(args[0], time)
        self.assertEqual(args[1], id_)
        self.assertEqual(args[2], action)
        self.assertEqual(args[3], event_type)
        self.assertIsInstance(args[4], str)

    def test_initialize(self):
        self.assertRaises(AssertionError, lambda: DeviceSchedule([]))

        ds = DeviceSchedule([(1, True), (1, False)], 'test', True)
        ds.initialize(self.env)
        self.assertEqual(ds.env, self.env)
        self.assertEqual(ds.is_active, True)
        self.assert_scheduled_event(-1, self.env.now + 1, ds.id, ds._update_status,
                                    EventType.OTHER_HIGH_PRIORITY)

    def test_re_initialize(self):
        ds = DeviceSchedule([(1, True)], 'test', True)
        ds.add_device(self.devices[0])
        ds.add_device(self.devices[1])
        ds.initialize(self.env)
        self.assertListEqual(ds._devices, self.devices)

        ds.remove_device(self.devices[0])
        self.assertCountEqual(ds._devices, [self.devices[1]])

        ds.initialize(self.env)
        self.assertEqual(ds.env, self.env)
        self.assertEqual(ds.is_active, True)
        self.assertCountEqual(ds._devices, self.devices)
        # With only one entry in the schedule there is no future change
        # to have been scheduled.
        self.assertEqual(len(self.env.schedule_event.call_args_list), 0)

    def test_schedule(self):
        schedule = []
        for i in range(1, 11):
            schedule.append((i, i % 1 == 0))
        ds = DeviceSchedule(schedule, is_cyclical = True)
        ds.initialize(self.env)

        for loops in range(2):
            for e in schedule:
                self.assertEqual(ds.is_active, e[1])
                self.assert_scheduled_event(-1, self.env.now + e[0], ds.id, ds._update_status,
                                    EventType.OTHER_HIGH_PRIORITY)
                self.env.now += e[0]
                ds._update_status()

    def test_acyclical_schedule(self):
        ds = DeviceSchedule([(1, True), (3, False)], is_cyclical = False)
        ds.initialize(self.env)

        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        self.assertEqual(ds.is_active, True)
        ds._update_status()
        self.assertEqual(ds.is_active, False)

        if len(self.env.schedule_event.call_args_list) == 2:
            # If a new update was scheduled then make sure it runs and
            # does not schedule another update.
            ds._update_status()
            self.assertEqual(len(self.env.schedule_event.call_args_list), 2)
        self.assertEqual(ds.is_active, False)


if __name__ == '__main__':
    unittest.main()
