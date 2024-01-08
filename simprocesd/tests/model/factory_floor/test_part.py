from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, System
from ....model.factory_floor import Asset, Part, PartFlowController, PartGenerator


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

    def test_part_generator(self):
        ids = []
        pg = PartGenerator('name', value = 100, quality = 3)
        # Make 10 parts and ensure attributes are set correctly.
        for i in range(10):
            new_part = pg.generate_part()
            self.assertNotIn(new_part.id, ids)
            ids.append(new_part.id)
            self.assertRegex(new_part.name, f'name_{i+1}')
            self.assertEqual(new_part.value, 100)
            self.assertEqual(new_part.quality, 3)


if __name__ == '__main__':
    unittest.main()
