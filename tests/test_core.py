from __future__ import annotations

from decimal import Decimal
import unittest

from pnf.core import PnFConfig, build_columns, calculate_logscale_box_size, calculate_step_box_size


class CoreTests(unittest.TestCase):
    def test_config_validation(self) -> None:
        with self.assertRaises(ValueError):
            PnFConfig(box_pct=0, reversal=3)
        with self.assertRaises(ValueError):
            PnFConfig(box_pct=0.01, reversal=0)
        with self.assertRaises(ValueError):
            PnFConfig(box_pct=0.01, reversal=3, method="open")
        with self.assertRaises(ValueError):
            PnFConfig(box_pct=0.01, reversal=3, scaling="linear")
        with self.assertRaises(ValueError):
            PnFConfig(box_pct=0.01, reversal=3, tick_size=0)

    def test_initial_column_waits_for_reversal_threshold(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3)
        columns = build_columns([100, 102.99], config)
        self.assertEqual(columns, [])

        columns = build_columns([100, 103], config)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].type, "X")
        self.assertEqual(columns[0].box_count, 3)
        self.assertEqual(columns[0].low, Decimal("101.00"))
        self.assertEqual(columns[0].high, Decimal("103.00"))
        self.assertEqual(columns[0].boxes, (Decimal("101.00"), Decimal("102.00"), Decimal("103.00")))

    def test_prices_are_rounded_to_nearest_cent(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3)
        columns = build_columns([Decimal("100.005"), Decimal("103.015")], config)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].boxes, (Decimal("101.01"), Decimal("102.01"), Decimal("103.01")))
        self.assertTrue(all(box.as_tuple().exponent == -2 for box in columns[0].boxes))

    def test_step_box_size_uses_tick_rounded_reference(self) -> None:
        config = PnFConfig(box_pct=0.0025, reversal=3)
        self.assertEqual(calculate_step_box_size(Decimal("100.005"), config), Decimal("0.250025"))

    def test_logscale_box_size_uses_tick_rounded_reference(self) -> None:
        config = PnFConfig(box_pct=0.0025, reversal=3, scaling="log")
        self.assertEqual(calculate_logscale_box_size(Decimal("100.005"), config), Decimal("0.250025"))

    def test_custom_tick_size_rounds_to_nearest_tick(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3, tick_size=Decimal("0.05"))
        columns = build_columns([Decimal("100.03"), Decimal("103.10")], config)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].boxes, (Decimal("101.05"), Decimal("102.05"), Decimal("103.05")))

    def test_logscale_box_size_rejects_invalid_reference(self) -> None:
        config = PnFConfig(box_pct=0.0025, reversal=3, scaling="log")
        with self.assertRaises(ValueError):
            calculate_logscale_box_size(0, config)

    def test_true_logscale_changes_box_size_each_box(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3, scaling="log")
        columns = build_columns([100, 105], config)
        self.assertEqual(len(columns), 1)
        self.assertEqual(
            columns[0].boxes,
            (Decimal("101.00"), Decimal("102.01"), Decimal("103.03"), Decimal("104.06")),
        )

    def test_initial_gap_uses_single_frozen_box_size(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3)
        columns = build_columns([100, 110], config)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].box_count, 10)
        self.assertEqual(columns[0].high, Decimal("110.00"))
        self.assertEqual(columns[0].boxes[-1], Decimal("110.00"))

    def test_extension_recalculates_only_at_next_update(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3)
        columns = build_columns([100, 103, 107.12], config)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].box_count, 7)
        self.assertEqual(
            columns[0].boxes[-4:],
            (
                Decimal("104.0300"),
                Decimal("105.0600"),
                Decimal("106.0900"),
                Decimal("107.1200"),
            ),
        )

    def test_exact_reversal_threshold_creates_reversal_column(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3)
        columns = build_columns([100, 103, 99.91], config)
        self.assertEqual([column.type for column in columns], ["X", "O"])
        self.assertEqual(columns[1].box_count, 3)
        self.assertEqual(columns[1].high, Decimal("101.9700"))
        self.assertEqual(columns[1].low, Decimal("99.9100"))

    def test_reversal_gap_creates_multiple_boxes(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3)
        columns = build_columns([100, 103, 96], config)
        self.assertEqual([column.type for column in columns], ["X", "O"])
        self.assertEqual(columns[1].box_count, 6)
        self.assertEqual(columns[1].low, Decimal("96.8200"))

    def test_missing_close_values_are_skipped_without_fill(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3)
        columns = build_columns([None, {"close": 100}, {"close": None}, {"close": 103}], config)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].start_index, 1)
        self.assertEqual(columns[0].end_index, 3)

    def test_high_low_extension_has_current_direction_priority(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3, method="high_low")
        data = [
            {"high": 100, "low": 100},
            {"high": 103, "low": 103},
            {"high": 104.03, "low": 99.91},
        ]
        columns = build_columns(data, config)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].type, "X")
        self.assertEqual(columns[0].high, Decimal("104.0300"))

    def test_high_low_can_reverse_when_no_extension_occurs(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3, method="high_low")
        data = [
            {"high": 100, "low": 100},
            {"high": 103, "low": 103},
            {"high": 102, "low": 99.91},
        ]
        columns = build_columns(data, config)
        self.assertEqual([column.type for column in columns], ["X", "O"])

    def test_high_low_close_can_use_close_when_high_low_are_missing(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3, method="high_low_close")
        data = [
            {"close": 100},
            {"close": 103},
        ]
        columns = build_columns(data, config)
        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].type, "X")

    def test_high_low_close_validates_close_inside_range(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3, method="high_low_close")
        with self.assertRaises(ValueError):
            build_columns([{"high": 100, "low": 99, "close": 101}], config)

    def test_large_dataset_is_deterministic(self) -> None:
        config = PnFConfig(box_pct=0.0025, reversal=3)
        data = [Decimal("100") + Decimal(index % 37) / Decimal("10") for index in range(100_000)]
        first = build_columns(data, config)
        second = build_columns(data, config)
        self.assertEqual(first, second)
        self.assertGreater(len(first), 0)

    def test_non_positive_price_raises(self) -> None:
        config = PnFConfig(box_pct=0.01, reversal=3)
        with self.assertRaises(ValueError):
            build_columns([100, 0], config)
