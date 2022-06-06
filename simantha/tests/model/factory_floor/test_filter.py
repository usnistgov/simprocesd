from unittest import TestCase
import unittest
from unittest.mock import MagicMock

from ....model import Environment, System
from ....model.factory_floor import Part, Machine, Filter


class FilterTestCase(TestCase):

    def setUp(self):
        self.sys = System()
        self.env = MagicMock(spec = Environment)
        self.env.now = 1
        self.upstream = [MagicMock(spec = Machine), MagicMock(spec = Machine)]
        self.downstream = [MagicMock(spec = Machine), MagicMock(spec = Machine)]
        for d in self.downstream:
            d.give_part.return_value = True

    def test_initialize(self):
        filter_ = Filter(lambda: True, 'name', self.upstream)
        self.assertIn(filter_, self.sys._assets)
        self.assertEqual(filter_.name, 'name')
        self.assertEqual(filter_.upstream, self.upstream)
        self.assertEqual(filter_.value, 0)

    def test_notify_upstream_of_available_space(self):
        filter_ = Filter(lambda: True, 'name', self.upstream)

        for u in self.upstream:
            u.space_available_downstream.assert_not_called()
        filter_.space_available_downstream()
        for u in self.upstream:
            u.space_available_downstream.assert_called_once()

    def test_pass_part(self):
        filter_ = Filter(lambda p: True)
        filter_._add_downstream(self.downstream[0])
        part = Part()

        self.assertTrue(filter_.give_part(part))
        # Ensure no events are generated.
        self.assertEqual(len(self.env.schedule_event.call_args_list), 0)
        self.downstream[0].give_part.assert_called_once_with(part)

    def test_pass_part_condition(self):
        filter_ = Filter(lambda p: p.value > 1)
        for d in self.downstream:
            filter_._add_downstream(d)
        bad_part = Part(value = 0)
        good_part = Part(value = 2)

        self.assertFalse(filter_.give_part(bad_part))
        self.downstream[0].give_part.assert_not_called()
        self.downstream[1].give_part.assert_not_called()

        self.assertTrue(filter_.give_part(good_part))
        self.downstream[0].give_part.assert_called_once_with(good_part)
        self.downstream[1].give_part.assert_not_called()

    def test_pass_part_blocked_downstream(self):
        filter_ = Filter(lambda p: True)
        for d in self.downstream:
            filter_._add_downstream(d)
        part1, part2 = Part(), Part()
        # First downstream does not accept part but second does.
        self.downstream[0].give_part.return_value = False
        self.assertTrue(filter_.give_part(part1))
        self.downstream[0].give_part.assert_called_once_with(part1)
        self.downstream[1].give_part.assert_called_once_with(part1)
        # Neither downstream will accept the part.
        self.downstream[1].give_part.return_value = False
        self.assertFalse(filter_.give_part(part2))
        self.assertEqual(len(self.downstream[0].give_part.call_args_list), 2)
        self.assertEqual(len(self.downstream[1].give_part.call_args_list), 2)


if __name__ == '__main__':
    unittest.main()
