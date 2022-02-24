from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from .. import add_side_effect_to_class_method
from ...model import Event, Environment, EventType
from ...utils import DataStorageType


class EnvironmentTestCase(TestCase):
    execution_order = []

    @staticmethod
    def execute_side_effect(event):
        EnvironmentTestCase.execution_order.append(event)

    def setUp(self):
        self.env = Environment('env', DataStorageType.MEMORY)
        self.action = MagicMock()
        # Clear the list between tests.
        EnvironmentTestCase.execution_order = []
        # When execute is called on any Event then that event will be
        # appended to EnvironmentTestCase.execution_order.
        add_side_effect_to_class_method(self, __name__ + '.Event.execute',
                                        Event.execute, self.execute_side_effect)

    def schedule_events(self):
        ''' Schedules 4 events with self.env.
        '''
        # WARNING: changing parameters may break tests.
        self.env.schedule_event(45, 0, MagicMock(), EventType.FAIL)
        self.env.schedule_event(50, 1, MagicMock(), EventType.OTHER_LOW)
        self.env.schedule_event(15, 2, MagicMock(), EventType.FAIL)
        self.env.schedule_event(20, 2, MagicMock(), EventType.RESTORE)
        self.env.schedule_event(50, 3, MagicMock(), EventType.FAIL)

    def test_initialize(self):
        self.assertEqual(self.env.simulation_data, {})
        self.assertEqual(self.env.name, 'env')
        self.assertEqual(self.env.now, 0)

    def test_file_storage(self):
        self.assertRaises(NotImplementedError,
                          lambda: Environment(simulation_data_storage_type = DataStorageType.FILE))

    def test_schedule_event(self):
        self.env.schedule_event(5, 45537, self.action, EventType.FAIL, 'test_msg')
        self.assertEqual(len(self.env._events), 1)

        event = self.env._events[0]
        self.assertEqual(event.time, 5)
        self.assertEqual(event.asset_id, 45537)
        self.assertEqual(event.action, self.action)
        self.assertEqual(event.event_type, EventType.FAIL)
        self.assertEqual(event.message, 'test_msg')
        self.assertEqual(event.status, '')
        self.assertEqual(event.paused_at, None)
        self.assertEqual(event.cancelled, False)
        self.assertEqual(event.executed, False)

    def test_schedule_event_times(self):
        self.env.now = 10
        self.assertRaises(ValueError,
                lambda: self.env.schedule_event(self.env.now - 1, 1, self.action))

        self.env.schedule_event(self.env.now, 1, self.action)
        self.env.schedule_event(self.env.now + 1, 1, self.action)
        self.assertEqual(len(self.env._events), 2)

    def test_step(self):
        self.schedule_events()
        events = sorted(self.env._events)
        self.env.step()

        self.assertEqual(self.env.now, events[0].time)
        self.assertEqual(len(self.execution_order), 1)
        self.assertEqual(self.execution_order[0], events[0])
        events[0].action.assert_called_once()

    def test_run(self):
        self.schedule_events()
        events = sorted(self.env._events)
        # last item of sorted events will have the latest scheduled time
        self.env.run(events[-1].time)
        self.assertEqual(self.env.now, events[-1].time)
        # +1 because run() adds a terminate event
        self.assertEqual(len(self.execution_order), len(events) + 1)
        # Ensure the execution order is correct, ignore terminate event.
        for i in range(len(self.execution_order) - 1):
            self.assertEqual(self.execution_order[i], events[i])
        # Calling run more than once throws an error.
        self.assertRaises(RuntimeError, lambda: self.env.run(10))

    def test_event_scheduled_after_simulation_end(self):
        self.schedule_events()
        events = sorted(self.env._events)

        last_event_time = events[-1].time + 1000
        action = MagicMock(autospec = True)
        self.env.schedule_event(last_event_time, 7357, action, EventType.PASS_PART)
        self.env.run(last_event_time - 1)

        self.assertEqual(self.env.now, last_event_time - 1)
        # Make sure new event was not executed.
        action.assert_not_called()
        for e in EnvironmentTestCase.execution_order:
            self.assertNotEqual(e.asset_id, 7357)

    def test_cancel_events(self):
        self.schedule_events()
        self.env.cancel_matching_events(1)
        self.env.cancel_matching_events(2)

        for e in self.env._events:
            if e.asset_id == 1 or e.asset_id == 2:
                self.assertTrue(e.cancelled, e)
            else:
                self.assertFalse(e.cancelled, e)

    def test_pause_events(self):
        self.schedule_events()
        self.env.pause_matching_events(2)

        for e in self.env._events:
            if e.asset_id == 2:
                self.assertEquals(e.paused_at, 0)
                self.assertIn(e, self.env._paused_events)
            else:
                self.assertEqual(e.paused_at, None)
                self.assertNotIn(e, self.env._paused_events)

    def test_unpause_events(self):
        self.schedule_events()
        events = sorted(self.env._events)

        self.env.pause_matching_events(0)
        self.env.step()
        self.env.unpause_matching_events(0)
        self.assertEqual(len(self.env._paused_events), 0)

        new_events_order = sorted(events)
        self.assertNotEqual(new_events_order, events)

        while len(self.env._events) > 0:
            self.env.step()

        self.assertEqual(len(self.execution_order), len(events))
        # Ensure right events ran and in the right order.
        for i in range(len(self.execution_order)):
            self.assertEqual(self.execution_order[i], new_events_order[i], f'i = {i}')

    def test_add_simple_datapoints(self):
        self.env.add_datapoint('label', 'asset_name', 1)
        self.env.add_datapoint('label', 'asset_name', 2)
        self.env.add_datapoint('label', 'asset_name2', 1)
        self.env.add_datapoint('label2', 'asset_name', 1)
        self.env.add_datapoint('label', 'asset_name', 3)

        self.assertCountEqual(self.env.simulation_data.keys(), ['label', 'label2'])
        self.assertCountEqual(self.env.simulation_data['label'].keys(),
                              ['asset_name', 'asset_name2'])
        self.assertCountEqual(self.env.simulation_data['label2'].keys(), ['asset_name'])
        self.assertListEqual(self.env.simulation_data['label']['asset_name'], [1, 2, 3])
        self.assertListEqual(self.env.simulation_data['label']['asset_name2'], [1])
        self.assertListEqual(self.env.simulation_data['label2']['asset_name'], [1])

    def test_add_list_datapoints(self):
        self.env.add_datapoint('label', 'asset_name', [1])
        self.env.add_datapoint('label', 'asset_name', [8, 3])
        self.env.add_datapoint('label', 'asset_name', [1, 4, 7, 3])

        self.assertListEqual(self.env.simulation_data['label']['asset_name'],
                             [[1], [8, 3], [1, 4, 7, 3]])


if __name__ == '__main__':
    unittest.main()
