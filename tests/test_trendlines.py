from __future__ import annotations

import unittest

from pnf.core import PnFConfig
from pnf.trendlines import bearish_resistance_line, bullish_support_line, is_line_broken
from tests.helpers import make_column


class TrendlineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = PnFConfig(box_pct=0.01, reversal=3)

    def test_bullish_support_line_anchors_to_lowest_o_and_breaks_on_full_box(self) -> None:
        columns = [
            make_column("X", "100", "102", 0, count=3),
            make_column("O", "98", "100", 1, count=3),
            make_column("X", "100", "103", 2, count=4),
            make_column("O", "100", "102", 3, count=3),
        ]
        line = bullish_support_line(columns, self.config)
        self.assertIsNotNone(line)
        assert line is not None
        self.assertEqual(line.anchor_column, 1)
        self.assertFalse(is_line_broken(line))

        broken_columns = columns + [make_column("O", "99", "101", 4, count=3)]
        broken = bullish_support_line(broken_columns, self.config)
        self.assertIsNotNone(broken)
        assert broken is not None
        self.assertEqual(broken.broken_at, 4)

    def test_bearish_resistance_line_anchors_to_highest_x_and_breaks_on_full_box(self) -> None:
        columns = [
            make_column("O", "98", "100", 0, count=3),
            make_column("X", "100", "102", 1, count=3),
            make_column("O", "97", "99", 2, count=3),
            make_column("X", "98", "100", 3, count=3),
        ]
        line = bearish_resistance_line(columns, self.config)
        self.assertIsNotNone(line)
        assert line is not None
        self.assertEqual(line.anchor_column, 1)
        self.assertFalse(is_line_broken(line))

        broken_columns = columns + [make_column("X", "99", "101", 4, count=3)]
        broken = bearish_resistance_line(broken_columns, self.config)
        self.assertIsNotNone(broken)
        assert broken is not None
        self.assertEqual(broken.broken_at, 4)
