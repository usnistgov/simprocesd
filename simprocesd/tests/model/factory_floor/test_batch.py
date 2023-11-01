from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment
from ....model.factory_floor import Part, PartProcessor, Batch


class BatchTestCase(TestCase):

    def test_initialize(self):
        env = Environment()
        part = Part()
        part.initialize(env)
        batch = Batch('name', [part])

        self.assertEqual(batch.name, 'name')
        self.assertEqual(len(batch.parts), 1)
        self.assertEqual(batch.parts[0], part)
        self.assertEqual(batch.routing_history, [])

    def test_make_copy(self):
        ids = []
        part = Part('p', 100, 3)
        part.add_routing_history(MagicMock(spec = PartProcessor))
        batch = Batch('b', [part])
        batches = [batch]

        for i in range(10):
            # Check Batch
            batches.append(batch.make_copy())
            self.assertNotIn(batches[-1].id, ids)
            ids.append(batches[-1].id)
            self.assertRegex(batches[-1].name, f'{batch.name}_{i+1}')
            self.assertEqual(batches[-1].value, 100)
            self.assertEqual(len(batches[-1].routing_history), 0)
            # Check Part in the Batch
            new_part = batches[-1].parts[0]
            self.assertNotIn(new_part.id, ids)
            ids.append(new_part.id)
            self.assertEqual(new_part.value, 100)
            self.assertEqual(new_part.quality, 3)
            self.assertEqual(len(new_part.routing_history), 0)

    def test_change_value(self):
        batch = Batch()
        self.assertRaises(NotImplementedError, lambda: batch.add_value('', 1))
        self.assertRaises(NotImplementedError, lambda: batch.add_cost('', 1))


if __name__ == '__main__':
    unittest.main()
