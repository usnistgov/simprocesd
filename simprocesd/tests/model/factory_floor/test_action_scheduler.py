from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, EventType, System
from ....model.factory_floor import ActionScheduler, PartProcessor


class ExtendedActionScheduler(ActionScheduler):

    def __init__(self, schedule, name = None, is_cyclical = True):
        super().__init__(schedule, name, is_cyclical)
        self.last_call = None
        self.calls = 0

    def default_action(self, obj, time, state):
        self.last_call = (obj, time, state)
        self.calls += 1


class ActionSchedulerTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 0
        self.objects = [MagicMock(), MagicMock()]
        self.object_dict = {self.objects[0]: None, self.objects[1]: None}

    def assert_scheduled_event(self, event_index, time, id_, action, event_type):
        args, kwargs = self.env.schedule_event.call_args_list[event_index]
        self.assertEqual(args[0], time)
        self.assertEqual(args[1], id_)
        self.assertEqual(args[2], action)
        self.assertEqual(args[3], event_type)
        self.assertIsInstance(args[4], str)

    def test_initialize(self):
        self.assertRaises(AssertionError, lambda: ActionScheduler([]))

        sched = ActionScheduler([(1, True), (1, False)], 'test', True)
        sched.initialize(self.env)
        self.assertEqual(sched.env, self.env)
        self.assertEqual(sched.current_state, True)
        self.assert_scheduled_event(-1, self.env.now + 1, sched.id, sched._update_state,
                                    EventType.OTHER_HIGH_PRIORITY)

    def test_register_unregister(self):
        sched = ActionScheduler([(1, True)], 'test', True)

        self.assertTrue(sched.register_object(self.objects[0]))
        self.assertFalse(sched.register_object(self.objects[0], self.objects[0].override_call))
        self.assertTrue(sched.register_object(self.objects[1]))

        self.assertTrue(sched.unregister_object(self.objects[0]))
        self.assertFalse(sched.unregister_object(self.objects[0]))

        self.assertTrue(sched.register_object(self.objects[0], self.objects[0].override_call))
        self.assertFalse(sched.register_object(self.objects[0], self.objects[0].override_call))

        self.assertTrue(sched.unregister_object(self.objects[1]))
        self.assertFalse(sched.unregister_object(self.objects[1]))

    def test_schedule(self):
        schedule = []
        for i in range(1, 11):
            schedule.append((i, 100 - i))
        sched = ExtendedActionScheduler(schedule, is_cyclical = True)
        sched.register_object(self.objects[0], self.objects[0].override_call)
        sched.register_object(self.objects[1])
        sched.initialize(self.env)

        expected_default_calls = 1
        for loops in range(2):
            for state_time, state in schedule:
                self.assertEqual(sched.current_state, state)
                self.assert_scheduled_event(-1, self.env.now + state_time, sched.id, sched._update_state,
                                    EventType.OTHER_HIGH_PRIORITY)
                # Assert calls for registered objects:
                # self.objects[0] has a custom function.
                self.assertEqual(len(self.objects[0].override_call.call_args_list), expected_default_calls)
                self.objects[0].override_call.assert_called_with(sched, self.objects[0], self.env.now, state)
                # self.objects[1] uses default class function.
                self.assertEqual(sched.calls, expected_default_calls)
                self.assertEqual(sched.last_call, (self.objects[1], self.env.now, state))
                # Updates to simulate next schedule progression.
                self.env.now += state_time
                sched._update_state()
                expected_default_calls += 1

    def test_acyclical_schedule(self):
        obj1 = PartProcessor()
        sched = ActionScheduler([(1, obj1), (3, 'banana')], is_cyclical = False)
        sched.initialize(self.env)

        self.assertEqual(len(self.env.schedule_event.call_args_list), 1)
        self.assertEqual(sched.current_state, obj1)
        sched._update_state()
        self.assertEqual(sched.current_state, 'banana')

        if len(self.env.schedule_event.call_args_list) == 2:
            # If a new update was scheduled then make sure it runs and
            # does not schedule another update.
            sched._update_state()
            self.assertEqual(len(self.env.schedule_event.call_args_list), 2)
        self.assertEqual(sched.current_state, 'banana')


if __name__ == '__main__':
    unittest.main()
