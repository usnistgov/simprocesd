from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, System
from ....model.factory_floor import Asset


class AssetTestCase(TestCase):

    def setUp(self):
        self.sys = System()

    def test_init_basic(self):
        asset = Asset('name', 99)
        self.assertEqual(asset.name, 'name')
        self.assertEqual(asset.value, 99)

    def test_init(self):
        assets = []
        ids = []
        # Make 100 assets and ensure IDs are unique.
        for i in range(100):
            assets.append(Asset())
            self.assertIn(assets[i], self.sys._assets)
            self.assertTrue(assets[i].id >= 0)
            self.assertNotIn(assets[i].id, ids)
            ids.append(assets[i].id)
            self.assertEqual(assets[i].name, f'Asset_{assets[i].id}')
            self.assertEqual(assets[i].value, 0)

    def test_initialize(self):
        a = Asset()
        self.assertRaises(TypeError, lambda: a.initialize(25))
        self.assertRaises(TypeError, lambda: a.initialize(Asset()))

        env = Environment()
        a.initialize(env)
        self.assertEqual(a.env, env)

    def test_add_value(self):
        a = Asset(value = 10)
        env = MagicMock(spec = Environment)
        a.initialize(env)

        env.now = 1
        a.add_value('label', 5.95)
        new_expected_value = 10 + 5.95
        expected = [('label', 1, 5.95, new_expected_value)]
        self.assertEqual(a.value_history, expected)
        self.assertEqual(a.value, new_expected_value)

        env.now = 5
        a.add_value('label2', 100)
        new_expected_value += 100
        expected.append(('label2', 5, 100, new_expected_value))
        self.assertEqual(a.value_history, expected)
        self.assertEqual(a.value, new_expected_value)

        # Value of 0 is ignored
        a.add_value('label3', 0)
        self.assertEqual(a.value_history, expected)
        a.add_cost('label4', 0)
        self.assertEqual(a.value_history, expected)

    def test_add_cost(self):
        a = Asset(value = 10)
        env = MagicMock(spec = Environment)
        a.initialize(env)

        env.now = 1
        a.add_cost('label', 3.50)
        new_expected_value = 10 - 3.50
        expected = [('label', 1, -3.50, new_expected_value)]
        self.assertEqual(a.value_history, expected)
        self.assertEqual(a.value, new_expected_value)

        env.now = 2
        a.add_cost('label2', 1)
        new_expected_value -= 1
        expected.append(('label2', 2, -1, new_expected_value))
        self.assertEqual(a.value_history, expected)
        self.assertEqual(a.value, new_expected_value)


if __name__ == '__main__':
    unittest.main()
