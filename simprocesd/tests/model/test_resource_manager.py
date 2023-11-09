from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ...model import Environment, ResourceManager


class ResourceManagerTestCase(TestCase):

    def setUp(self):
        self.rm = ResourceManager()
        self.env_mock = MagicMock(spec = Environment)
        self.env_mock.now = 0
        # Prevents warnings from reserved resources going out of scope
        # before releasing their resources.
        self.env_mock.is_simulation_in_progress.return_value = False

    def test_init(self):
        self.assert_resource_state_helper({'non_existend_resource': (0, 0)})

    def test_initialize(self):
        self.rm.add_resources('a', 5)
        self.env_mock.add_datapoint.assert_not_called()

        self.rm.initialize(self.env_mock)
        self.env_mock.add_datapoint.assert_called_once_with('resource_update', 'a',
                                                            (self.env_mock.now, 0, 5))

    def test_reserve_resources(self):
        self.rm.add_resources('a', 5)
        self.rm.initialize(self.env_mock)

        self.assertRaises(ValueError, lambda: self.rm.reserve_resources({'a':-1}))
        # Zero amount can always be reserved.
        rr = self.rm.reserve_resources({'non_existent': 0})
        self.assertNotEqual(rr, None)
        self.assertDictEqual(rr.reserved_resources, {})
        # Reserve a resource that doesn't exist.
        rr = self.rm.reserve_resources({'b': 1})
        self.assertEqual(rr, None)
        self.assert_resource_state_helper({'a': (0, 5)})

        rr1 = self.rm.reserve_resources({'a': 2})
        self.assertNotEqual(rr1, None)
        self.assertDictEqual(rr1.reserved_resources, {'a': 2})
        self.assert_resource_state_helper({'a': (2, 5)})
        # Reserve more than is remaining.
        rr = self.rm.reserve_resources({'a': 4})
        self.assertEqual(rr, None)
        self.assert_resource_state_helper({'a': (2, 5)})

        rr2 = self.rm.reserve_resources({'a': 3})
        self.assertNotEqual(rr2, None)
        self.assertDictEqual(rr2.reserved_resources, {'a': 3})
        self.assert_resource_state_helper({'a': (5, 5)})

        rr1.release()
        self.assertDictEqual(rr1.reserved_resources, {})
        self.assert_resource_state_helper({'a': (3, 5)})
        rr2.release()
        self.assertDictEqual(rr2.reserved_resources, {})
        self.assert_resource_state_helper({'a': (0, 5)})

    def test_reserve_multiple_resources(self):
        self.rm.add_resources('test', 99)
        self.rm.add_resources('super', 5)
        self.rm.initialize(self.env_mock)
        # Reserve a resource that doesn't exist.
        rr = self.rm.reserve_resources({'super test': 1})
        self.assertEqual(rr, None)
        self.assert_resource_state_helper({'test': (0, 99), 'super': (0, 5)})

        rr1 = self.rm.reserve_resources({'test': 50, 'super': 1})
        self.assertNotEqual(rr1, None)
        self.assertDictEqual(rr1.reserved_resources, {'test': 50, 'super': 1})
        self.assert_resource_state_helper({'test': (50, 99), 'super': (1, 5)})
        # Reserve more than is remaining.
        rr = self.rm.reserve_resources({'test': 50, 'super': 1})
        self.assertEqual(rr, None)
        self.assert_resource_state_helper({'test': (50, 99), 'super': (1, 5)})

        rr2 = self.rm.reserve_resources({'super': 4, 'test': 10})
        self.assertNotEqual(rr2, None)
        self.assertDictEqual(rr2.reserved_resources, {'super': 4, 'test': 10})
        self.assert_resource_state_helper({'test': (60, 99), 'super': (5, 5)})

        rr1.release()
        self.assertDictEqual(rr1.reserved_resources, {})
        self.assert_resource_state_helper({'test': (10, 99), 'super': (4, 5)})
        rr2.release()
        self.assertDictEqual(rr2.reserved_resources, {})
        self.assert_resource_state_helper({'test': (0, 99), 'super': (0, 5)})

    def test_remove_resource(self):
        self.rm.add_resources('a', 10)
        self.rm.add_resources('b', 1)
        self.rm.initialize(self.env_mock)

        rr1 = self.rm.reserve_resources({'b': 1})
        self.assertNotEqual(rr1, None)
        self.assert_resource_state_helper({'a': (0, 10), 'b': (1, 1)})

        self.rm.add_resources('a', -5)
        self.rm.add_resources('a', -1)
        self.assert_resource_state_helper({'a': (0, 4), 'b': (1, 1)})

        self.rm.add_resources('b', -1)
        self.assert_resource_state_helper({'a': (0, 4), 'b': (1, 0)})

        rr = self.rm.reserve_resources({'b': 1})
        self.assertEqual(rr, None)

        rr1.release()
        self.assert_resource_state_helper({'a': (0, 4), 'b': (0, 0)})

        rr = self.rm.reserve_resources({'b': 1})
        self.assertEqual(rr, None)

    def test_reserve_resources_callback(self):
        self.rm.initialize(self.env_mock)
        cb = MagicMock()
        self.rm.reserve_resources_with_callback({'donuts': 3, 'coffee': 1}, cb)

        self.rm._check_pending_requests()
        cb.assert_not_called()

        self.rm.add_resources('donuts', 2)
        self.rm._check_pending_requests()
        cb.assert_not_called()

        self.rm.add_resources('coffee', 2)
        self.rm._check_pending_requests()
        cb.assert_not_called()

        self.rm.add_resources('donuts', 2)
        self.rm._check_pending_requests()
        cb.assert_called_once_with(self.rm, {'donuts': 3, 'coffee': 1})

    def test_reserve_resources_with_callback(self):
        self.rm.initialize(self.env_mock)
        rr = []

        def callback(rm, request, holder = rr):
            holder.append(rm.reserve_resources(request))

        self.rm.reserve_resources_with_callback({'a': 3, 'b': 1}, callback)
        self.rm._check_pending_requests()
        self.assertEqual(len(rr), 0)

        self.rm.add_resources('a', 3)
        self.rm.add_resources('b', 1)
        self.assert_resource_state_helper({'a': (0, 3), 'b': (0, 1)})
        self.rm._check_pending_requests()
        self.assertEqual(len(rr), 1)
        self.assertDictEqual(rr[0].reserved_resources, {'a': 3, 'b': 1})
        self.assert_resource_state_helper({'a': (3, 3), 'b': (1, 1)})

    def test_request_release(self):
        self.rm.add_resources('a', 5)
        self.rm.add_resources('b', 5)
        self.rm.initialize(self.env_mock)

        rr1 = self.rm.reserve_resources({'a': 2, 'b': 5})
        self.assertNotEqual(rr1, None)
        self.assertDictEqual(rr1.reserved_resources, {'a': 2, 'b': 5})

        rr1.release({'a': 2, 'b': 3})
        self.assertDictEqual(rr1.reserved_resources, {'b': 2})

        self.assertRaises(KeyError, lambda: rr1.release({'a': 2}))
        self.assertRaises(ValueError, lambda: rr1.release({'b':-1}))
        self.assertRaises(ValueError, lambda: rr1.release({'b': 3}))
        self.assertDictEqual(rr1.reserved_resources, {'b': 2})

        rr1.release({'b': 2})
        self.assertDictEqual(rr1.reserved_resources, {})

    def test_merge_requests(self):
        self.rm.add_resources('a', 5)
        self.rm.add_resources('b', 5)
        self.rm.initialize(self.env_mock)

        rr1 = self.rm.reserve_resources({'a': 2, 'b': 1})
        self.assertDictEqual(rr1.reserved_resources, {'a': 2, 'b': 1})
        rr2 = self.rm.reserve_resources({'a': 3, 'b': 2})
        self.assertDictEqual(rr2.reserved_resources, {'a': 3, 'b': 2})
        self.assert_resource_state_helper({'a': (5, 5), 'b': (3, 5)})

        rr1.merge(rr2)
        self.assertDictEqual(rr1.reserved_resources, {'a': 5, 'b': 3})
        self.assertDictEqual(rr2.reserved_resources, {})
        self.assert_resource_state_helper({'a': (5, 5), 'b': (3, 5)})

        rr2.release()
        self.assert_resource_state_helper({'a': (5, 5), 'b': (3, 5)})
        rr1.release()
        self.assert_resource_state_helper({'a': (0, 5), 'b': (0, 5)})

    def assert_resource_state_helper(self, resource_state_dictionary):
        for resource_name, state in resource_state_dictionary.items():
            self.assertEqual(self.rm.get_resource_usage(resource_name), state[0])
            self.assertEqual(self.rm.get_resource_capacity(resource_name), state[1])


if __name__ == '__main__':
    unittest.main()
