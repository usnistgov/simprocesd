import gc
from io import StringIO
from unittest import TestCase
import unittest
from unittest.mock import MagicMock, patch

from .. import add_side_effect_to_class_method
from ...model import Environment, System
from ...model.factory_floor import Asset, Sink
from ...utils import DataStorageType


class SystemTestCase(TestCase):

    def setUp(self):
        System._instance = None
        self.sys = System(DataStorageType.MEMORY)
        # Mock out the Environment class.
        self.env_mock = MagicMock(spec = Environment)
        self.env_mock.now = 0
        self.sys._env = self.env_mock
        # Mock out time getting method to keep it predictable.
        self.time_mock = add_side_effect_to_class_method(self, 'time.time')
        # Calling time.time() will first return 0, then 1, then 2...
        self.time_mock.side_effect = [i for i in range(10)]

    def test_initialize(self):
        sys = System(DataStorageType.MEMORY)
        assets = [Asset()]  # Adds to System automatically.

        self.assertEqual(sys._assets, assets)
        self.assertEqual(sys._env._simulation_data_storage_type, DataStorageType.MEMORY)

    def test_simulation_data(self):
        self.env_mock.simulation_data = {'label': {'asset_name': [1, 5, 9]}}

        def override_simulation_data():
            self.sys.simulation_data = {}

        # Test that trying to override simulation_data throws an error.
        self.assertRaises(AttributeError, override_simulation_data)
        self.assertEqual(self.sys.simulation_data, self.env_mock.simulation_data)

    @patch('sys.stdout', new_callable = StringIO)
    def test_simulate(self, stdout_mock):
        sink = MagicMock(spec = Sink)
        sink.received_parts_count = 56
        self.sys._assets.append(sink)
        self.sys.simulate(1, False, False, True)

        self.env_mock.run.assert_called_once_with(1, trace = False)
        # Net received parts does not change so it is 0.
        self.assertEqual(stdout_mock.getvalue(),
                'Simulation finished in 1.00s\nParts received by sink/s: 0\n')

    @patch('sys.stdout', new_callable = StringIO)
    def test_simulate_no_print(self, stdout_mock):
        self.sys.simulate(99, False, True, False)

        self.env_mock.run.assert_called_once_with(99, trace = True)
        self.assertEqual(stdout_mock.getvalue(), '')

    @patch('sys.stdout', new_callable = StringIO)  # Consume print statements.
    def test_simulate_old_system(self, stdout_mock):
        sys = System()
        self.assertRaises(RuntimeError, lambda: self.sys.simulate(1))

    def test_simulate_initialize(self):
        sink = MagicMock(spec = Sink)
        self.sys._assets.append(sink)

        self.sys.simulate(5, print_summary = False)
        sink.initialize.assert_called_once_with(self.env_mock)

        self.sys.simulate(5, print_summary = False)
        sink.initialize.assert_called_once_with(self.env_mock)

        self.sys.simulate(5, reset = True, print_summary = False)
        self.assertEqual(len(sink.initialize.call_args_list), 2)

    def test_get_net_value(self):
        sink = Sink()
        sink._value = 100
        Asset(value = 50)
        Asset(value = -33)

        self.assertEqual(self.sys.get_net_value_of_assets(), 100 + 50 - 33)


if __name__ == '__main__':
    unittest.main()
