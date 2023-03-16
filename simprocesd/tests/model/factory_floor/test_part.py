from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment
from ....model.factory_floor import Part, Machine


class PartTestCase(TestCase):

    def test_initialize(self):
        part = Part('name', 2, 5)
        part.initialize(Environment())
        self.assertEqual(part.name, 'name')
        self.assertEqual(part.value, 2)
        self.assertEqual(part.quality, 5)
        self.assertEqual(part.routing_history, [])

    def test_re_initialize(self):
        part = Part('name', 2, 5)
        env = Environment()
        part.initialize(env)

        machine = MagicMock(spec = Machine)
        part.add_cost('', 1)
        part.quality = 3.14
        part.add_routing_history(machine)
        self.assertEqual(part.value, 2 - 1)
        self.assertEqual(part.quality, 3.14)
        self.assertEqual(part.routing_history, [machine])

        self.assertRaises(AssertionError, lambda: part.initialize(Environment()))
        part.initialize(env)
        self.assertEqual(part.value, 2)
        self.assertEqual(part.quality, 5)
        self.assertEqual(part.routing_history, [])

    def test_make_copy(self):
        ids = []
        part = Part('name', 100, 3)
        part.add_routing_history(MagicMock(spec = Machine))
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
