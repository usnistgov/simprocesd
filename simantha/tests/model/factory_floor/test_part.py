from unittest import TestCase
import unittest

from ....model.factory_floor import Asset, Part


class PartTestCase(TestCase):

    def test_init(self):
        part = Part('name', 2, 5)
        self.assertEqual(part.name, 'name')
        self.assertEqual(part.value, 2)
        self.assertEqual(part.quality, 5)
        self.assertEqual(len(part.routing_history), 0)

    def test_copy(self):
        ids = []
        part = Part('name', 100, 3)
        part.routing_history.append(Asset())
        parts = [part]
        # Make 10 parts and ensure attributes are set correctly.
        for i in range(10):
            parts.append(part.copy())
            self.assertNotIn(parts[-1].id, ids)
            ids.append(parts[-1].id)
            self.assertRegex(parts[-1].name, f'{part.name}_{i+1}')
            self.assertEqual(parts[-1].value, 100)
            self.assertEqual(parts[-1].quality, 3)
            self.assertEqual(len(parts[-1].routing_history), 0)


if __name__ == '__main__':
    unittest.main()
