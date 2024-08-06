import concurrent.futures

from io import StringIO
import unittest
from unittest import TestCase
from unittest.mock import MagicMock, patch

from .. import add_side_effect_to_class_method
from ...model import Environment, System, ResourceManager
from ...model.factory_floor import Asset, PartHandler, PartProcessor, Sink
from dataclasses import replace


class SystemTestCase(TestCase):

    def setUp(self):
        System._instance = None
        self.sys = System()
        # Mock out the Environment class.
        self.env_mock = MagicMock(spec = Environment)
        self.env_mock.resource_manager = MagicMock(spec = ResourceManager)
        self.env_mock.now = 0
        self.sys._env = self.env_mock

    def test_initialize(self):
        res_manager = ResourceManager()
        sys = System(res_manager)
        assets = [Asset()]  # Adds to System automatically.

        self.assertEqual(sys._assets, assets)
        self.assertEqual(sys.env.resource_manager, res_manager)

    def test_simulation_data(self):
        self.env_mock.simulation_data = {'label': {'asset_name': [1, 5, 9]}}

        def override_simulation_data():
            self.sys.simulation_data = {}

        # Test that trying to override simulation_data throws an error.
        self.assertRaises(AttributeError, override_simulation_data)
        self.assertEqual(self.sys.simulation_data, self.env_mock.simulation_data)

    @patch('sys.stdout', new_callable = StringIO)
    def test_simulate(self, stdout_mock):
        # Mock out time getting method to keep it predictable.
        time_mock = add_side_effect_to_class_method(self, 'time.time')
        # Calling time.time() will first return 0, then 1, then 2...
        time_mock.side_effect = [i for i in range(10)]

        sink = MagicMock(spec = Sink)
        sink.received_parts_count = 56
        self.sys.add_asset(sink)
        self.sys.simulate(1, False, True)

        self.env_mock.run.assert_called_once_with(1, trace = False)
        # Net received parts does not change so it is 0.
        self.assertEqual(stdout_mock.getvalue(),
                'Simulation finished in 1.00s\nParts received by sink(s): 0\n')

    @patch('sys.stdout', new_callable = StringIO)
    def test_simulate_no_print(self, stdout_mock):
        self.sys.simulate(99, trace = True, print_summary = False)

        self.env_mock.run.assert_called_once_with(99, trace = True)
        self.assertEqual(stdout_mock.getvalue(), '')

    @patch('sys.stdout', new_callable = StringIO)  # Consume print statements.
    def test_simulate_old_system(self, stdout_mock):
        sys = System()
        self.assertRaises(RuntimeError, lambda: self.sys.simulate(1))

    def test_simulate_initialize(self):
        sink = MagicMock(spec = Sink)
        self.sys.add_asset(sink)

        self.sys.simulate(5, print_summary = False)
        self.env_mock.resource_manager.initialize.assert_called_once_with(self.env_mock)
        sink.initialize.assert_called_once_with(self.env_mock)
        # Continue the simulation for another 5 time units.
        self.sys.simulate(5, print_summary = False)
        self.env_mock.resource_manager.initialize.assert_called_once_with(self.env_mock)
        sink.initialize.assert_called_once_with(self.env_mock)

    def test_simulate_initialize_after_start(self):
        self.sys.simulate(5, print_summary = False)

        sink = MagicMock(spec = Sink)
        self.sys.add_asset(sink)
        sink.initialize.assert_called_once_with(self.env_mock)

    def test_get_net_value(self):
        sink = Sink()
        sink._value = 100
        Asset(value = 50)
        Asset(value = -33)

        self.assertEqual(self.sys.get_net_value_of_assets(), 100 + 50 - 33)

    def test_find_asset(self):
        assets = [Asset('asset'), PartProcessor('machine'), Sink('sink')]
        self.assertEqual(self.sys.find_assets(name = 'sink'), assets[2:])
        self.assertEqual(self.sys.find_assets(id_ = assets[1].id), assets[1:2])
        self.assertEqual(self.sys.find_assets(type_ = PartProcessor), assets[1:2])
        self.assertEqual(self.sys.find_assets(subtype = Asset), assets[0:])
        self.assertEqual(self.sys.find_assets(subtype = PartHandler), assets[1:])
        self.assertEqual(self.sys.find_assets(subtype = Sink), assets[2:])

    def test_find_asset_mix(self):
        assets = [Asset('machine'), PartProcessor('machine'), Sink('machine')]
        self.assertEqual(self.sys.find_assets(name = 'machine', subtype = PartHandler), assets[1:])
        self.assertEqual(self.sys.find_assets(name = 'machine', type_ = PartProcessor), [assets[1]])

    def test_simulate_multiple_times_bad_input(self):
        simulation_func = MagicMock(spec = callable)
        self.assertRaises(AssertionError, lambda: System.simulate_multiple_times(
            simulation_func, 0, 1))
        self.assertRaises(AssertionError, lambda: System.simulate_multiple_times(
            simulation_func, 1, -1))

    def test_simulate_multiple_times(self):
        future_mock = MagicMock(spec = concurrent.futures.Future)
        # Mock out the call to create jobs.
        submit_job_mock = add_side_effect_to_class_method(self, 'concurrent.futures.ProcessPoolExecutor.submit',
                                                          replacement = lambda *args, **kwargs: future_mock)

        simulation_func = MagicMock(spec = callable)
        extra_arg = 'a string!'
        extra_kwarg = 'a kstring!'
        num_of_runs = 3
        rtn_systems = System.simulate_multiple_times(simulation_func, num_of_runs, 2, extra_arg, a = extra_kwarg)

        self.assertEqual(len(rtn_systems), num_of_runs)
        for i in range(num_of_runs):
            args, kwargs = submit_job_mock.call_args_list[i]
            self.assertEqual(args[2], simulation_func)
            self.assertEqual(args[3], i)
            self.assertEqual(args[4], extra_arg)
            self.assertEqual(kwargs['a'], extra_kwarg)

        self.assertEqual(len(future_mock.result.call_args_list), num_of_runs)

    def test_simulate_multiple_times_same_thread(self):
        simulation_func = MagicMock(spec = callable)
        num_of_runs = 3
        rtn_systems = System.simulate_multiple_times(simulation_func, num_of_runs, 0)

        systems = []
        for i in range(num_of_runs):
            args, kwargs = simulation_func.call_args_list[i]
            self.assertEqual(type(args[0]), System)
            systems.append(args[0])
            self.assertEqual(args[1], i)

        self.assertEqual(rtn_systems, systems)


if __name__ == '__main__':
    unittest.main()
