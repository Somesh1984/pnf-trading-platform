from __future__ import annotations

from dataclasses import fields
from decimal import Decimal
import unittest

from pnf.core import PnFConfig
from pnf.counts import CountTarget, horizontal_count, vertical_count
from pnf.patterns import PatternSignal
from tests.helpers import make_column


class CountTests(unittest.TestCase):
    def test_count_target_field_order_is_stable(self) -> None:
        self.assertEqual(
            [field.name for field in fields(CountTarget)],
            [
                "kind",
                "direction",
                "start_column",
                "end_column",
                "count",
                "box_size",
                "base_price",
                "target",
            ],
        )

    def test_horizontal_count_uses_explicit_column_range(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "104", 2),
        ]
        config = PnFConfig(box_pct=0.01, reversal=3)

        target = horizontal_count(columns, config, 0, 2, "bullish")

        self.assertEqual(target.kind, "horizontal")
        self.assertEqual(target.direction, "bullish")
        self.assertEqual(target.start_column, 0)
        self.assertEqual(target.end_column, 2)
        self.assertEqual(target.count, 3)
        self.assertEqual(target.box_size, Decimal("1.0400"))
        self.assertEqual(target.base_price, Decimal("104"))
        self.assertEqual(target.target, Decimal("113.36"))

    def test_horizontal_count_bearish_uses_end_column_low_as_base(self) -> None:
        columns = [
            make_column("O", "97", "100", 0, count=4),
            make_column("X", "98", "101", 1, count=4),
            make_column("O", "96", "99", 2, count=4),
        ]
        config = PnFConfig(box_pct=0.01, reversal=3)

        target = horizontal_count(columns, config, 0, 2, "bearish")

        self.assertEqual(target.kind, "horizontal")
        self.assertEqual(target.direction, "bearish")
        self.assertEqual(target.start_column, 0)
        self.assertEqual(target.end_column, 2)
        self.assertEqual(target.count, 3)
        self.assertEqual(target.box_size, Decimal("0.9600"))
        self.assertEqual(target.base_price, Decimal("96"))
        self.assertEqual(target.target, Decimal("87.36"))

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
        self.assertEqual(target.kind, "vertical")
        self.assertEqual(target.direction, "bullish")
        self.assertEqual(target.start_column, 2)
        self.assertEqual(target.end_column, 2)
        self.assertEqual(target.count, 4)
        self.assertEqual(target.box_size, Decimal("1.0400"))
        self.assertEqual(target.base_price, Decimal("104"))
        self.assertEqual(target.target, Decimal("116.48"))

    def test_vertical_count_bearish_uses_first_valid_breakdown(self) -> None:
        columns = [
            make_column("O", "97", "100", 0, count=4),
            make_column("X", "98", "101", 1, count=4),
            make_column("O", "96", "99", 2, count=4),
            make_column("X", "97", "100", 3, count=4),
            make_column("O", "95", "98", 4, count=4),
        ]
        config = PnFConfig(box_pct=0.01, reversal=3)
        patterns = [
            PatternSignal("double_bottom_breakdown", "bearish", 2, Decimal("97"), Decimal("96"), (0, 1)),
            PatternSignal("bearish_catapult", "bearish", 4, Decimal("96"), Decimal("95"), (0, 2, 3)),
        ]

        target = vertical_count(columns, config, patterns, "bearish")

        self.assertIsNotNone(target)
        assert target is not None
        self.assertEqual(target.kind, "vertical")
        self.assertEqual(target.direction, "bearish")
        self.assertEqual(target.start_column, 2)
        self.assertEqual(target.end_column, 2)
        self.assertEqual(target.count, 4)
        self.assertEqual(target.box_size, Decimal("0.9600"))
        self.assertEqual(target.base_price, Decimal("96"))
        self.assertEqual(target.target, Decimal("84.48"))

    def test_vertical_count_direction_filter_can_return_none(self) -> None:
        columns = [
            make_column("X", "100", "103", 0, count=4),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "104", 2, count=4),
        ]
        config = PnFConfig(box_pct=0.01, reversal=3)
        patterns = [PatternSignal("double_top_breakout", "bullish", 2, Decimal("103"), Decimal("104"), (0, 1))]

        self.assertIsNone(vertical_count(columns, config, patterns, "bearish"))

    def test_count_input_validation_is_clear(self) -> None:
        columns = [make_column("X", "100", "103", 0)]
        config = PnFConfig(box_pct=0.01, reversal=3)

        with self.assertRaises(ValueError):
            horizontal_count(columns, config, 0, 0, "sideways")
        with self.assertRaises(ValueError):
            vertical_count(columns, config, direction="sideways")

        invalid_ranges = [(-1, 0), (0, 1), (1, 0)]
        for start_column, end_column in invalid_ranges:
            with self.subTest(start_column=start_column, end_column=end_column):
                with self.assertRaises(ValueError):
                    horizontal_count(columns, config, start_column, end_column, "bullish")

    def test_horizontal_and_vertical_counts_are_deterministic(self) -> None:
        columns = [
            make_column("X", "100", "103", 0, count=4),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "104", 2, count=4),
        ]
        config = PnFConfig(box_pct=0.01, reversal=3)
        patterns = [PatternSignal("double_top_breakout", "bullish", 2, Decimal("103"), Decimal("104"), (0, 1))]

        self.assertEqual(
            horizontal_count(columns, config, 0, 2, "bullish"),
            horizontal_count(columns, config, 0, 2, "bullish"),
        )
        self.assertEqual(
            vertical_count(columns, config, patterns, "bullish"),
            vertical_count(columns, config, patterns, "bullish"),
        )
