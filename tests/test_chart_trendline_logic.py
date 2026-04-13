import unittest
from typing import Any

import numpy as np

from chart_pnf import PointFigureChart


TRENDLINE_KEYS = {"bounded", "type", "length", "column index", "box index"}
BOUNDED_VALUES = {"external", "internal"}
TRENDLINE_TYPES = {"bullish support", "bearish resistance"}
UPWARD_ZIGZAG = [100, 103, 100, 104, 101, 105, 102, 106, 103, 107]
DOWNWARD_ZIGZAG = [100, 97, 100, 96, 99, 95, 98, 94, 97, 93]
SCALINGS = ("abs", "cla", "atr", "log", "log_compounding")


def _chart(close: list[int], scaling: str) -> PointFigureChart:
    if scaling == "atr":
        close_values = np.array(close, dtype=float)
        return PointFigureChart(
            ts={"close": close_values, "high": close_values + 1, "low": close_values - 1},
            method="cl",
            reversal=3,
            boxsize=3,
            scaling=scaling,
        )

    return PointFigureChart(
        ts={"close": close},
        method="cl",
        reversal=3,
        boxsize=1,
        scaling=scaling,
    )


def _assert_trendline_schema(testcase: unittest.TestCase, trendlines: dict[str, Any]) -> None:
    testcase.assertEqual(set(trendlines), TRENDLINE_KEYS)
    sizes = {len(values) for values in trendlines.values()}
    testcase.assertEqual(len(sizes), 1)
    if not sizes or sizes == {0}:
        return

    testcase.assertTrue(set(trendlines["bounded"]).issubset(BOUNDED_VALUES))
    testcase.assertTrue(set(trendlines["type"]).issubset(TRENDLINE_TYPES))
    testcase.assertTrue(np.all(trendlines["length"] > 0))
    testcase.assertTrue(np.all(trendlines["column index"] >= 0))
    testcase.assertTrue(np.all(trendlines["box index"] >= 0))


class ChartTrendlineLogicTests(unittest.TestCase):
    def test_all_supported_scalings_return_deterministic_trendline_schema(self) -> None:
        for scaling in SCALINGS:
            for close in (UPWARD_ZIGZAG, DOWNWARD_ZIGZAG):
                for mode in ("strong", "weak"):
                    with self.subTest(scaling=scaling, close=close, mode=mode):
                        first = _chart(close, scaling)
                        second = _chart(close, scaling)
                        matrix_before = first.matrix.copy()
                        boxscale_before = first.boxscale.copy()

                        first_trendlines = first.get_trendlines(length=4, mode=mode)
                        second_trendlines = second.get_trendlines(length=4, mode=mode)

                        _assert_trendline_schema(self, first_trendlines)
                        self.assertGreater(len(first_trendlines["type"]), 0)
                        for key in TRENDLINE_KEYS:
                            np.testing.assert_array_equal(first_trendlines[key], second_trendlines[key])
                        np.testing.assert_array_equal(first.matrix, matrix_before)
                        np.testing.assert_array_equal(first.boxscale, boxscale_before)

    def test_absolute_scaling_upward_example_has_bullish_support(self) -> None:
        chart = _chart(UPWARD_ZIGZAG, "abs")

        trendlines = chart.get_trendlines(length=4, mode="weak")

        _assert_trendline_schema(self, trendlines)
        self.assertIn("bullish support", trendlines["type"].tolist())

    def test_absolute_scaling_downward_example_has_bearish_resistance(self) -> None:
        chart = _chart(DOWNWARD_ZIGZAG, "abs")

        trendlines = chart.get_trendlines(length=4, mode="weak")

        _assert_trendline_schema(self, trendlines)
        self.assertIn("bearish resistance", trendlines["type"].tolist())

    def test_log_scaling_trendlines_are_deterministic_and_non_mutating(self) -> None:
        close = [100, 103, 99.91, 104.03, 100.91, 105.07, 101.92]
        first = _chart(close, "log")
        second = _chart(close, "log")
        matrix_before = first.matrix.copy()
        boxscale_before = first.boxscale.copy()

        first_trendlines = first.get_trendlines(length=4, mode="strong")
        second_trendlines = second.get_trendlines(length=4, mode="strong")

        _assert_trendline_schema(self, first_trendlines)
        for key in TRENDLINE_KEYS:
            np.testing.assert_array_equal(first_trendlines[key], second_trendlines[key])
        np.testing.assert_array_equal(first.matrix, matrix_before)
        np.testing.assert_array_equal(first.boxscale, boxscale_before)

    def test_trendline_minimum_length_warnings_return_valid_schema(self) -> None:
        chart = _chart(UPWARD_ZIGZAG, "abs")

        with self.assertWarns(UserWarning):
            weak = chart.get_trendlines(length=3, mode="weak")
        with self.assertWarns(UserWarning):
            strong = chart.get_trendlines(length=2, mode="strong")

        _assert_trendline_schema(self, weak)
        _assert_trendline_schema(self, strong)


if __name__ == "__main__":
    unittest.main()
