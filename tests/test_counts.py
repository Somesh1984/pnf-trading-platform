from __future__ import annotations

from decimal import Decimal
import unittest

from pnf.core import PnFConfig
from pnf.counts import horizontal_count, vertical_count
from pnf.patterns import PatternSignal
from tests.helpers import make_column


class CountTests(unittest.TestCase):
    def test_horizontal_count_uses_explicit_column_range(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "104", 2),
        ]
        config = PnFConfig(box_pct=0.01, reversal=3)
        target = horizontal_count(columns, config, 0, 2, "bullish")
        self.assertEqual(target.count, 3)
        self.assertEqual(target.base_price, Decimal("104"))
        self.assertEqual(target.target, Decimal("113.36"))

    def test_vertical_count_uses_first_valid_breakout_only(self) -> None:
        columns = [
            make_column("X", "100", "103", 0, count=4),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "104", 2, count=4),
            make_column("O", "101", "103", 3),
            make_column("X", "102", "105", 4, count=4),
        ]
        config = PnFConfig(box_pct=0.01, reversal=3)
        patterns = [
            PatternSignal("double_top_breakout", "bullish", 2, Decimal("103"), Decimal("104"), (0, 1)),
            PatternSignal("bullish_catapult", "bullish", 4, Decimal("104"), Decimal("105"), (0, 2, 3)),
        ]
        target = vertical_count(columns, config, patterns, "bullish")
        self.assertIsNotNone(target)
        assert target is not None
        self.assertEqual(target.start_column, 2)
        self.assertEqual(target.target, Decimal("116.48"))
