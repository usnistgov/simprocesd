from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment
from ....model.factory_floor import Asset


class AssetTestCase(TestCase):

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
            self.assertTrue(assets[i].id >= 0)
            self.assertNotIn(assets[i].id, ids)
            ids.append(assets[i].id)
            self.assertRegex(assets[i].name, f'Asset\'>_{assets[i].id}')
            self.assertEqual(assets[i].value, 0)

    def test_initialize(self):
        a = Asset()
        self.assertRaises(TypeError, lambda: a.initialize(25))
        self.assertRaises(TypeError, lambda: a.initialize(Asset()))

        env = Environment()
        a.initialize(env)
        self.assertEqual(a._env, env)

    def test_initialize_called_twice(self):
        a = Asset()
        a.initialize(Environment())
        self.assertRaises(AssertionError, lambda: a.initialize(Environment()))

    def test_add_value(self):
        a = Asset(value = 10)
        env = MagicMock(spec = Environment)
        a.initialize(env)

        env.now = 1
        a.add_value('label', 5.95)
        expected = [('label', 1, 5.95)]
        self.assertEqual(a.value_history, expected)
        self.assertEqual(a.value, 10 + 5.95)

        env.now = 5
        a.add_value('label2', 100)
        expected.append(('label2', 5, 100))
        self.assertEqual(a.value_history, expected)
        self.assertEqual(a.value, 10 + 5.95 + 100)

    def test_add_cost(self):
        a = Asset()  # value = 0
        env = MagicMock(spec = Environment)
        a.initialize(env)

        env.now = 1
        a.add_cost('label', 3.50)
        expected = [('label', 1, -3.50)]
        self.assertEqual(a.value_history, expected)
        self.assertEqual(a.value, -3.50)

        env.now = 2
        a.add_cost('label2', 1)
        expected.append(('label2', 2, -1))
        self.assertEqual(a.value_history, expected)
        self.assertEqual(a.value, -3.50 - 1)


if __name__ == '__main__':
    unittest.main()
