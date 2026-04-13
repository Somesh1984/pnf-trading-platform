from __future__ import annotations

import unittest

from pnf.patterns import (
    detect_bearish_catapults,
    detect_bullish_catapults,
    detect_double_bottom_breakdowns,
    detect_double_top_breakouts,
    detect_patterns,
    detect_triple_bottom_breakdowns,
    detect_triple_top_breakouts,
)
from pnf.core import PnFConfig
from tests.helpers import make_column


class PatternTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = PnFConfig(box_pct=0.01, reversal=3)

    def test_double_top_requires_strict_breakout(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "103", 2),
        ]
        self.assertEqual(detect_double_top_breakouts(columns, self.config), [])

        columns[-1] = make_column("X", "101", "104", 2)
        signals = detect_double_top_breakouts(columns, self.config)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].name, "double_top_breakout")

    def test_double_bottom_requires_strict_breakdown(self) -> None:
        columns = [
            make_column("O", "97", "100", 0),
            make_column("X", "98", "101", 1),
            make_column("O", "97", "100", 2),
        ]
        self.assertEqual(detect_double_bottom_breakdowns(columns, self.config), [])

        columns[-1] = make_column("O", "96", "100", 2)
        signals = detect_double_bottom_breakdowns(columns, self.config)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].name, "double_bottom_breakdown")

    def test_triple_top_uses_equal_prior_highs(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "103", 2),
            make_column("O", "100", "102", 3),
            make_column("X", "101", "104", 4),
        ]
        signals = detect_triple_top_breakouts(columns, self.config)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].name, "triple_top_breakout")

    def test_triple_bottom_uses_equal_prior_lows(self) -> None:
        columns = [
            make_column("O", "97", "100", 0),
            make_column("X", "98", "101", 1),
            make_column("O", "97", "100", 2),
            make_column("X", "98", "101", 3),
            make_column("O", "96", "100", 4),
        ]
        signals = detect_triple_bottom_breakdowns(columns, self.config)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].name, "triple_bottom_breakdown")

    def test_catapult_patterns_are_confirmed_by_prior_columns(self) -> None:
        bullish = [
            make_column("X", "100", "103", 0),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "104", 2),
            make_column("O", "101", "103", 3),
            make_column("X", "102", "105", 4),
        ]
        bearish = [
            make_column("O", "97", "100", 0),
            make_column("X", "98", "101", 1),
            make_column("O", "96", "100", 2),
            make_column("X", "98", "100", 3),
            make_column("O", "95", "99", 4),
        ]
        self.assertEqual(detect_bullish_catapults(bullish, self.config)[0].name, "bullish_catapult")
        self.assertEqual(detect_bearish_catapults(bearish, self.config)[0].name, "bearish_catapult")

    def test_detect_patterns_only_returns_supported_names(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("O", "100", "102", 1),
            make_column("X", "101", "104", 2),
        ]
        names = {signal.name for signal in detect_patterns(columns, self.config)}
        self.assertEqual(names, {"double_top_breakout"})
