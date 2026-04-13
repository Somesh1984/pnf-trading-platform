from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from decimal import Decimal
import unittest

from pnf.core import PnFConfig
from pnf.strategy import TradeSignal, generate_trades
from tests.helpers import make_column


class StrategyTests(unittest.TestCase):
    def test_trade_signal_output_fields_are_stable(self) -> None:
        self.assertEqual(
            [field.name for field in fields(TradeSignal)],
            ["direction", "entry", "stop_loss", "target", "pattern_name", "column_index", "count_kind"],
        )

        signal = TradeSignal(
            direction="bullish",
            entry=Decimal("104"),
            stop_loss=Decimal("100"),
            target=Decimal("116.48"),
            pattern_name="double_top_breakout",
            column_index=2,
            count_kind="vertical",
        )

        with self.assertRaises(FrozenInstanceError):
            setattr(signal, "direction", "bearish")

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
        self.assertEqual(trades[0].pattern_name, "double_top_breakout")
        self.assertEqual(trades[0].column_index, 2)
        self.assertEqual(trades[0].count_kind, "vertical")
        self.assertIsInstance(trades[0].entry, Decimal)
        self.assertIsInstance(trades[0].stop_loss, Decimal)
        self.assertIsInstance(trades[0].target, Decimal)

    def test_strategy_bearish_trade_output_fields_are_stable(self) -> None:
        columns = [
            make_column("O", "97", "100", 0, count=4),
            make_column("X", "98", "100", 1),
            make_column("O", "96", "99", 2, count=4),
        ]

        trades = generate_trades(columns, PnFConfig(box_pct=0.01, reversal=3))

        self.assertEqual(len(trades), 1)
        self.assertEqual(trades[0].direction, "bearish")
        self.assertEqual(trades[0].entry, Decimal("96"))
        self.assertEqual(trades[0].stop_loss, Decimal("100"))
        self.assertEqual(trades[0].target, Decimal("84.48"))
        self.assertEqual(trades[0].pattern_name, "double_bottom_breakdown")
        self.assertEqual(trades[0].column_index, 2)
        self.assertEqual(trades[0].count_kind, "vertical")
        self.assertIsInstance(trades[0].entry, Decimal)
        self.assertIsInstance(trades[0].stop_loss, Decimal)
        self.assertIsInstance(trades[0].target, Decimal)

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
