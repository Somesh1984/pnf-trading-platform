from __future__ import annotations

from dataclasses import fields
from decimal import Decimal
from typing import Any
import unittest

from pnf.core import PnFConfig
from pnf.levels import PriceLevel, detect_horizontal_levels
from tests.helpers import make_column


class LevelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = PnFConfig(box_pct=0.01, reversal=3)

    def test_detects_horizontal_resistance_and_support_with_minimum_touches(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("O", "99", "102", 1),
            make_column("X", "101", "103", 2),
            make_column("O", "99", "102", 3),
            make_column("X", "100", "103", 4),
            make_column("O", "99", "102", 5),
        ]
        levels = detect_horizontal_levels(columns, self.config)
        self.assertEqual({level.kind for level in levels}, {"resistance", "support"})
        self.assertTrue(all(level.touches == 3 for level in levels))

    def test_price_level_output_fields_are_stable(self) -> None:
        self.assertEqual(
            [field.name for field in fields(PriceLevel)],
            ["kind", "price", "box", "touches", "column_indices", "start_column", "end_column"],
        )

    def test_resistance_uses_x_column_highs_and_support_uses_o_column_lows(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("O", "99", "102", 1),
            make_column("X", "101", "103", 2),
            make_column("O", "99", "102", 3),
            make_column("X", "100", "103", 4),
            make_column("O", "99", "102", 5),
        ]

        levels = detect_horizontal_levels(columns, self.config)
        resistance = next(level for level in levels if level.kind == "resistance")
        support = next(level for level in levels if level.kind == "support")

        self.assertEqual(resistance.price, Decimal("103"))
        self.assertEqual(resistance.box, 1)
        self.assertEqual(resistance.touches, 3)
        self.assertEqual(resistance.column_indices, (0, 2, 4))
        self.assertEqual(resistance.start_column, 0)
        self.assertEqual(resistance.end_column, 4)
        self.assertEqual(support.price, Decimal("99"))
        self.assertEqual(support.box, 0)
        self.assertEqual(support.touches, 3)
        self.assertEqual(support.column_indices, (1, 3, 5))
        self.assertEqual(support.start_column, 1)
        self.assertEqual(support.end_column, 5)

    def test_two_touches_do_not_create_level_by_default(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("O", "99", "102", 1),
            make_column("X", "101", "103", 2),
            make_column("O", "99", "102", 3),
        ]

        self.assertEqual(detect_horizontal_levels(columns, self.config), [])

    def test_cluster_threshold_is_in_box_units(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("X", "100", "104", 1),
            make_column("X", "100", "103", 2),
        ]
        self.assertEqual(detect_horizontal_levels(columns, self.config, cluster_threshold_boxes=0), [])
        levels = detect_horizontal_levels(columns, self.config, cluster_threshold_boxes=1)
        self.assertEqual(len(levels), 1)
        self.assertEqual(levels[0].kind, "resistance")
        self.assertEqual(levels[0].price, Decimal("103"))
        self.assertEqual(levels[0].box, 0)
        self.assertEqual(levels[0].touches, 3)
        self.assertEqual(levels[0].column_indices, (0, 2, 1))

    def test_levels_are_sorted_deterministically(self) -> None:
        columns = [
            make_column("O", "99", "102", 0),
            make_column("X", "100", "105", 1),
            make_column("O", "99", "102", 2),
            make_column("X", "100", "105", 3),
            make_column("O", "99", "102", 4),
            make_column("X", "100", "105", 5),
            make_column("X", "100", "103", 6),
            make_column("X", "100", "103", 7),
            make_column("X", "100", "103", 8),
        ]

        levels = detect_horizontal_levels(columns, self.config)

        self.assertEqual(
            [(level.start_column, level.kind, level.price) for level in levels],
            [(0, "support", Decimal("99")), (1, "resistance", Decimal("105")), (6, "resistance", Decimal("103"))],
        )

    def test_level_detection_is_deterministic(self) -> None:
        columns = [
            make_column("X", "100", "103", 0),
            make_column("O", "99", "102", 1),
            make_column("X", "101", "103", 2),
            make_column("O", "99", "102", 3),
            make_column("X", "100", "103", 4),
            make_column("O", "99", "102", 5),
        ]

        first = detect_horizontal_levels(columns, self.config)
        second = detect_horizontal_levels(columns, self.config)

        self.assertEqual(first, second)

    def test_levels_reject_weak_configuration(self) -> None:
        with self.assertRaises(ValueError):
            detect_horizontal_levels([make_column("X", "100", "103", 0)], self.config, min_touches=2)

    def test_levels_reject_negative_cluster_threshold(self) -> None:
        with self.assertRaises(ValueError):
            detect_horizontal_levels(
                [make_column("X", "100", "103", 0)],
                self.config,
                cluster_threshold_boxes=-1,
            )

    def test_levels_reject_invalid_config_type(self) -> None:
        invalid_config: Any = object()

        with self.assertRaises(TypeError):
            detect_horizontal_levels([make_column("X", "100", "103", 0)], config=invalid_config)
