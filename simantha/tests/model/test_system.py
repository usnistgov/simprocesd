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
        self.sys = System([], DataStorageType.MEMORY)
        # Mock out the Environment class.
        self.env_mock = MagicMock(spec = Environment)
        self.sys._env = self.env_mock
        # Mock out time getting method to keep it predictable.
        self.time_mock = add_side_effect_to_class_method(self, 'time.time')
        # calling time.time() will first return 0 then 1.
        self.time_mock.side_effect = [0, 1]

    def test_initialize(self):
        objects = [Asset()]
        sys = System(objects, DataStorageType.MEMORY)

        self.assertEqual(sys._objects, objects)
        self.assertEqual(sys._env._simulation_data_storage_type, DataStorageType.MEMORY)

    def test_simulation_data(self):
        self.env_mock.simulation_data = {'label': {'asset_name': [1, 5, 9]}}

        def override_simulation_data():
            self.sys.simulation_data = {}

        # Test that trying to override simulation_data throws an error.
        self.assertRaises(RuntimeError, override_simulation_data)
        self.assertEqual(self.sys.simulation_data, self.env_mock.simulation_data)

    @patch('sys.stdout', new_callable = StringIO)
    def test_simulate(self, stdout_mock):
        self.sys.simulate(99, True, False)

        self.env_mock.run.assert_called_once_with(99, trace = True)
        self.assertEqual(stdout_mock.getvalue(), '')

    @patch('sys.stdout', new_callable = StringIO)
    def test_simulate_print(self, stdout_mock):
        sink = Sink()
        sink._received_parts_count = 56
        self.sys._objects.append(sink)
        self.sys.simulate(1, False, True)

        self.env_mock.run.assert_called_once_with(1, trace = False)
        self.assertEqual(stdout_mock.getvalue(),
                         'Simulation finished in 1.00s\nParts produced: 56\n')

    def test_get_net_value(self):
        sink = Sink()
        sink._value = 100
        self.sys._objects.append(sink)
        self.sys._objects.append(Asset(value = 50))
        self.sys._objects.append(Asset(value = -33))

        self.assertEqual(self.sys.get_net_value_of_objects(), 100 + 50 - 33)


if __name__ == '__main__':
    unittest.main()
