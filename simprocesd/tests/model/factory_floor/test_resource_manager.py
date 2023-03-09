from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, ResourceManager


class ResourceManagerTestCase(TestCase):

    def setUp(self):
        self.rm = ResourceManager()
        self.env_mock = MagicMock(spec = Environment)
        self.env_mock.now = 0

    def test_init(self):
        self.assertEqual(len(self.rm.available_resources.items()), 0)

    def test_initialize(self):
        self.rm.add_resources('a', 5)
        self.env_mock.add_datapoint.assert_not_called()

        self.rm.initialize(self.env_mock)
        self.env_mock.add_datapoint.assert_called_once_with('resource_update', 'a',
                                                            (self.env_mock.now, 5))

    def test_re_initialize(self):
        self.rm.add_resources('a', 5)
        self.rm.add_resources('b', 2)
        self.rm.initialize(self.env_mock)

        self.rm.add_resources('a', 1)
        rr = self.rm.reserve_resources({'b': 1})
        self.assertDictEqual(self.rm.available_resources, {'a': 6, 'b': 1})

        self.rm.initialize(self.env_mock)
        self.assertDictEqual(self.rm.available_resources, {'a': 5, 'b': 2})

        # If ResourceManager was reinitialized that means the simulation
        # was restarted so releasing previously reserved resources does
        # not make sense.
        self.assertRaises(RuntimeError, lambda: rr.release())

    def test_reserve_resources(self):
        self.rm.add_resources('a', 5)
        self.rm.initialize(self.env_mock)
        # Reserve a resource that doesn't exist.
        rr = self.rm.reserve_resources({'b': 1})
        self.assertEqual(rr, None)
        self.assertDictEqual(self.rm.available_resources, {'a': 5})

        rr1 = self.rm.reserve_resources({'a': 2})
        self.assertNotEqual(rr1, None)
        self.assertDictEqual(rr1.reserved_resources, {'a': 2})
        self.assertDictEqual(self.rm.available_resources, {'a': 3})
        # Reserve more than is remaining.
        rr = self.rm.reserve_resources({'a': 4})
        self.assertEqual(rr, None)
        self.assertDictEqual(self.rm.available_resources, {'a': 3})

        rr2 = self.rm.reserve_resources({'a': 3})
        self.assertNotEqual(rr2, None)
        self.assertDictEqual(rr2.reserved_resources, {'a': 3})
        self.assertDictEqual(self.rm.available_resources, {'a': 0})

        rr1.release()
        self.assertDictEqual(rr1.reserved_resources, {'a': 0})
        self.assertDictEqual(self.rm.available_resources, {'a': 2})
        rr2.release()
        self.assertDictEqual(rr2.reserved_resources, {'a': 0})
        self.assertDictEqual(self.rm.available_resources, {'a': 5})

    def test_reserve_multiple_resources(self):
        self.rm.add_resources('test', 99)
        self.rm.add_resources('super', 5)
        self.rm.initialize(self.env_mock)
        # Reserve a resource that doesn't exist.
        rr = self.rm.reserve_resources({'super test': 1})
        self.assertEqual(rr, None)
        self.assertDictEqual(self.rm.available_resources, {'test': 99, 'super': 5})

        rr1 = self.rm.reserve_resources({'test': 50, 'super': 1})
        self.assertNotEqual(rr1, None)
        self.assertDictEqual(rr1.reserved_resources, {'test': 50, 'super': 1})
        self.assertDictEqual(self.rm.available_resources, {'test': 49, 'super': 4})
        # Reserve more than is remaining.
        rr = self.rm.reserve_resources({'test': 50, 'super': 1})
        self.assertEqual(rr, None)
        self.assertDictEqual(self.rm.available_resources, {'test': 49, 'super': 4})

        rr2 = self.rm.reserve_resources({'super': 4, 'test': 10})
        self.assertNotEqual(rr2, None)
        self.assertDictEqual(rr2.reserved_resources, {'super': 4, 'test': 10})
        self.assertDictEqual(self.rm.available_resources, {'test': 39, 'super': 0})

        rr1.release()
        self.assertDictEqual(rr1.reserved_resources, {'test': 0, 'super': 0})
        self.assertDictEqual(self.rm.available_resources, {'test': 89, 'super': 1})
        rr2.release()
        self.assertDictEqual(rr2.reserved_resources, {'test': 0, 'super': 0})
        self.assertDictEqual(self.rm.available_resources, {'test': 99, 'super': 5})

    def test_reserve_resources_with_callback(self):
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
        cb.assert_called_once_with({'donuts': 3, 'coffee': 1})


if __name__ == '__main__':
    unittest.main()
