from __future__ import annotations

from decimal import Decimal
import unittest

from pnf.core import PnFConfig
from pnf.strategy import generate_trades
from tests.helpers import make_column


class StrategyTests(unittest.TestCase):
    def test_strategy_requires_confirmed_pattern_and_count(self) -> None:
        columns = [
            make_column("X", "100", "103", 0, count=4),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "104", 2, count=4),
        ]
        trades = generate_trades(columns, PnFConfig(box_pct=0.01, reversal=3))
        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].direction, "bullish")
        self.assertEqual(trades[0].entry, Decimal("104"))
        self.assertEqual(trades[0].stop_loss, Decimal("100"))
        self.assertEqual(trades[0].target, Decimal("116.48"))

    def test_strategy_avoids_overtrading_same_direction(self) -> None:
        columns = [
            make_column("X", "100", "103", 0, count=4),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "104", 2, count=4),
            make_column("O", "101", "103", 3),
            make_column("X", "102", "105", 4, count=4),
        ]
        trades = generate_trades(columns, PnFConfig(box_pct=0.01, reversal=3))
        self.assertEqual(len([trade for trade in trades if trade.direction == "bullish"]), 1)
