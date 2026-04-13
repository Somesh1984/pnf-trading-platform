from __future__ import annotations

from collections.abc import Sequence
import unittest

import numpy as np

from chart_pnf import PointFigureChart


COUNT_KEYS = {
    "column index",
    "box index",
    "box",
    "trend",
    "type",
    "length",
    "anchor column",
    "anchor box",
    "target",
    "reward",
    "risk 1",
    "risk 2",
    "ratio 1",
    "ratio 2",
    "quality",
}
NUMERIC_KEYS = COUNT_KEYS - {"type"}
SCALINGS = ("abs", "cla", "atr", "log", "log_compounding")
COUNT_CLOSE = [100.0, 103.0, 100.0, 104.0, 101.0, 105.0, 102.0, 106.0, 103.0, 107.0, 100.0, 108.0, 101.0, 109.0]


def _chart(close: Sequence[float], scaling: str, reversal: int = 3) -> PointFigureChart:
    if scaling == "atr":
        close_values = np.array(close, dtype=float)
        return PointFigureChart(
            ts={"close": close_values, "high": close_values + 1.0, "low": close_values - 1.0},
            method="cl",
            reversal=reversal,
            boxsize=3,
            scaling=scaling,
        )

    return PointFigureChart(
        ts={"close": list(close)},
        method="cl",
        reversal=reversal,
        boxsize=1,
        scaling=scaling,
    )


def _assert_count_schema(testcase: unittest.TestCase, counts: dict[str, np.ndarray]) -> None:
    testcase.assertEqual(set(counts), COUNT_KEYS)
    lengths = {len(values) for values in counts.values()}
    testcase.assertEqual(len(lengths), 1)


def _assert_numeric_values_are_finite(testcase: unittest.TestCase, counts: dict[str, np.ndarray]) -> None:
    if len(counts["target"]) == 0:
        return

    for key in NUMERIC_KEYS:
        with testcase.subTest(key=key):
            values = np.asarray(counts[key], dtype=float)
            testcase.assertTrue(np.all(np.isfinite(values)))


class ChartCountLogicTests(unittest.TestCase):
    def test_get_counts_returns_stable_schema_for_all_supported_scalings(self) -> None:
        for scaling in SCALINGS:
            with self.subTest(scaling=scaling):
                chart = _chart(COUNT_CLOSE, scaling)

                counts = chart.get_counts(MinLength=5)

                _assert_count_schema(self, counts)
                _assert_numeric_values_are_finite(self, counts)

    def test_get_counts_is_deterministic_for_all_supported_scalings(self) -> None:
        for scaling in SCALINGS:
            with self.subTest(scaling=scaling):
                first = _chart(COUNT_CLOSE, scaling).get_counts(MinLength=5)
                second = _chart(COUNT_CLOSE, scaling).get_counts(MinLength=5)

                for key in COUNT_KEYS:
                    np.testing.assert_array_equal(first[key], second[key])

    def test_get_counts_does_not_mutate_matrix_or_boxscale(self) -> None:
        chart = _chart(COUNT_CLOSE, "log")
        matrix_before = chart.matrix.copy()
        boxscale_before = chart.boxscale.copy()

        chart.get_counts(MinLength=5)

        np.testing.assert_array_equal(chart.matrix, matrix_before)
        np.testing.assert_array_equal(chart.boxscale, boxscale_before)

    def test_min_length_below_five_uses_existing_minimum_behavior(self) -> None:
        low_minimum = _chart(COUNT_CLOSE, "abs").get_counts(MinLength=1)
        normal_minimum = _chart(COUNT_CLOSE, "abs").get_counts(MinLength=5)

        for key in COUNT_KEYS:
            np.testing.assert_array_equal(low_minimum[key], normal_minimum[key])

    def test_reversal_one_count_path_is_crash_free(self) -> None:
        close = [100.0, 101.0, 100.0, 101.0, 100.0, 102.0, 101.0, 103.0, 102.0, 104.0]
        chart = _chart(close, "abs", reversal=1)

        counts = chart.get_counts(MinLength=5)

        _assert_count_schema(self, counts)
        _assert_numeric_values_are_finite(self, counts)

    def test_absolute_scaling_example_has_vertical_count_output(self) -> None:
        counts = _chart(COUNT_CLOSE, "abs").get_counts(MinLength=5)

        _assert_count_schema(self, counts)
        self.assertIn("vertical", counts["type"].tolist())
        self.assertTrue(np.all(np.asarray(counts["target"], dtype=float) > np.asarray(counts["box"], dtype=float)))
