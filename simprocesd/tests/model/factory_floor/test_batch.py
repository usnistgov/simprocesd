from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment
from ....model.factory_floor import Batch, Part, PartFlowController


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

    def test_change_value(self):
        batch = Batch()
        self.assertRaises(NotImplementedError, lambda: batch.add_value('', 1))
        self.assertRaises(NotImplementedError, lambda: batch.add_cost('', 1))

    def test_modify_routing_history(self):
        part1, part2 = Part(), Part()
        device1, device2 = [MagicMock(spec = PartFlowController) for i in range(2)]
        part1.add_routing_history(device1)
        batch = Batch('name', [part1, part2])

        batch.add_routing_history(device2)
        self.assertEqual(part1.routing_history, [device1, device2])
        self.assertEqual(part2.routing_history, [device2])

        batch.remove_from_routing_history(-1)
        self.assertEqual(part1.routing_history, [device1])
        self.assertEqual(part2.routing_history, [])

        batch.add_routing_history(device2)
        batch.remove_from_routing_history(0)
        self.assertEqual(part1.routing_history, [device2])
        self.assertEqual(part2.routing_history, [])


if __name__ == '__main__':
    unittest.main()
