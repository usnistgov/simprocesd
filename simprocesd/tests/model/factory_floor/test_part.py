from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, System
from ....model.factory_floor import Part, PartFlowController, Asset


class PartTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 0

    def test_initialize(self):
        part = Part('name', 2, 5)
        part.initialize(self.env)
        self.assertEqual(part.name, 'name')
        self.assertEqual(part.value, 2)
        self.assertEqual(part.quality, 5)
        self.assertEqual(part.routing_history, [])

    def test_add_routing_history(self):
        part = Part()
        d1, d2 = MagicMock(spec = PartFlowController), MagicMock(spec = PartFlowController)
        part.initialize(self.env)

        self.assertEqual([], part.routing_history)
        part.add_routing_history(d1)
        self.assertEqual([d1], part.routing_history)
        part.add_routing_history(d2)
        self.assertEqual([d1, d2], part.routing_history)
        part.add_routing_history(d1)
        self.assertEqual([d1, d2, d1], part.routing_history)

        self.assertRaises(TypeError, lambda: part.add_routing_history(Asset()))
        self.assertRaises(TypeError, lambda: part.add_routing_history('test'))

    def test_remove_routing_history(self):
        part = Part()
        d1, d2 = MagicMock(spec = PartFlowController), MagicMock(spec = PartFlowController)
        part.initialize(self.env)
        for i in range (3):
            part.add_routing_history(d1)
            part.add_routing_history(d2)
        self.assertEqual([d1, d2, d1, d2, d1, d2], part.routing_history)

        part.remove_from_routing_history(0)
        self.assertEqual([d2, d1, d2, d1, d2], part.routing_history)
        part.remove_from_routing_history(-3)
        self.assertEqual([d2, d1, d1, d2], part.routing_history)

        self.assertRaises(IndexError, lambda: part.remove_from_routing_history(4))

    def test_make_copy(self):
        ids = []
        part = Part('name', 100, 3)
        part.initialize(self.env)
        part.add_routing_history(MagicMock(spec = PartFlowController))
        parts = [part]
        # Make 10 parts and ensure attributes are set correctly.
        for i in range(10):
            parts.append(part.make_copy())
            self.assertNotIn(parts[-1].id, ids)
            ids.append(parts[-1].id)
            self.assertRegex(parts[-1].name, f'{part.name}_{i+1}')
            self.assertEqual(parts[-1].value, 100)
            self.assertEqual(parts[-1].quality, 3)
            self.assertEqual(len(parts[-1].routing_history), 0)


if __name__ == '__main__':
    unittest.main()
