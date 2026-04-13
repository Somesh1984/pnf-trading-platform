import unittest

import numpy as np

from chart_pnf import PointFigureChart
from chart_pnf.chart_shared import SIGNAL_TYPES


def _close_chart(close: list[float], scaling: str = "abs") -> PointFigureChart:
    return PointFigureChart(
        ts={"close": close},
        method="cl",
        reversal=3,
        boxsize=1,
        scaling=scaling,
    )


def _nonzero_signal_columns(signals: dict[str, np.ndarray]) -> np.ndarray:
    return np.where(signals["width"] != 0)[0]


def _assert_signal_schema(testcase: unittest.TestCase, signals: dict[str, np.ndarray], column_count: int) -> None:
    expected_keys = {"box index", "top box index", "bottom box index", "type", "width", "ts index"}
    testcase.assertEqual(set(signals), expected_keys)
    for key in expected_keys:
        testcase.assertEqual(len(signals[key]), column_count)


class ChartPatternSignalLogicTests(unittest.TestCase):
    def test_bullish_double_top_style_breakout_fields(self) -> None:
        chart = _close_chart([100, 103, 100, 103, 104])

        breakouts = chart.get_breakouts()

        self.assertEqual(breakouts["trend"].tolist(), [1])
        self.assertEqual(breakouts["type"].tolist(), ["conti"])
        self.assertEqual(breakouts["hits"].tolist(), [2])
        self.assertEqual(breakouts["width"].tolist(), [3])

    def test_bearish_double_bottom_style_breakout_fields(self) -> None:
        chart = _close_chart([100, 97, 100, 97, 96])

        breakouts = chart.get_breakouts()

        self.assertEqual(breakouts["trend"].tolist(), [-1])
        self.assertEqual(breakouts["type"].tolist(), ["conti"])
        self.assertEqual(breakouts["hits"].tolist(), [2])
        self.assertEqual(breakouts["width"].tolist(), [3])

    def test_double_breakout_signal_types_match_signal_names(self) -> None:
        bullish = _close_chart([100, 103, 100, 103, 104])
        bearish = _close_chart([100, 97, 100, 97, 96])

        bullish_signals = bullish.get_double_breakouts()
        bearish_signals = bearish.get_double_breakouts()

        np.testing.assert_array_equal(_nonzero_signal_columns(bullish_signals), np.array([2]))
        np.testing.assert_array_equal(_nonzero_signal_columns(bearish_signals), np.array([2]))
        self.assertEqual(bullish_signals["type"][2], 2)
        self.assertEqual(SIGNAL_TYPES[int(bullish_signals["type"][2])], "Double Top Breakout")
        self.assertEqual(bearish_signals["type"][2], 3)
        self.assertEqual(SIGNAL_TYPES[int(bearish_signals["type"][2])], "Double Bottom Breakdown")

    def test_triple_breakout_signal_types_match_signal_names(self) -> None:
        bullish = _close_chart([100, 103, 100, 103, 100, 104])
        bearish = _close_chart([100, 97, 100, 97, 100, 96])

        bullish_signals = bullish.get_triple_breakouts()
        bearish_signals = bearish.get_triple_breakouts()

        np.testing.assert_array_equal(_nonzero_signal_columns(bullish_signals), np.array([4]))
        np.testing.assert_array_equal(_nonzero_signal_columns(bearish_signals), np.array([4]))
        self.assertEqual(bullish_signals["type"][4], 4)
        self.assertEqual(SIGNAL_TYPES[int(bullish_signals["type"][4])], "Triple Top Breakout")
        self.assertEqual(bearish_signals["type"][4], 5)
        self.assertEqual(SIGNAL_TYPES[int(bearish_signals["type"][4])], "Triple Bottom Breakdown")

    def test_get_signals_handles_double_and_triple_examples(self) -> None:
        examples = [
            ([100, 103, 100, 103, 104], 2, 2),
            ([100, 97, 100, 97, 96], 2, 3),
            ([100, 103, 100, 103, 100, 104], 4, 4),
            ([100, 97, 100, 97, 100, 96], 4, 5),
        ]

        for close, column_index, signal_type in examples:
            with self.subTest(close=close):
                signals = _close_chart(close).get_signals()
                self.assertIn(column_index, _nonzero_signal_columns(signals))
                self.assertEqual(signals["type"][column_index], signal_type)

    def test_all_public_signal_methods_return_valid_signal_schema(self) -> None:
        methods = [
            "get_buy_sell_signals",
            "get_triangles",
            "get_high_low_poles",
            "get_traps",
            "get_asc_desc_triple_breakouts",
            "get_catapults",
            "get_reversed_signals",
            "get_double_breakouts",
            "get_triple_breakouts",
            "get_spread_triple_breakouts",
            "get_quadruple_breakouts",
            "get_signals",
        ]
        examples = [
            [100, 103, 100, 103, 104],
            [100, 97, 100, 97, 96],
            [100, 103, 100, 103, 100, 104],
            [100, 97, 100, 97, 100, 96],
            [100, 103, 100, 104, 101, 105, 102, 106, 103, 107],
            [100, 97, 100, 96, 99, 95, 98, 94, 97, 93],
        ]

        for method in methods:
            for close in examples:
                with self.subTest(method=method, close=close):
                    chart = _close_chart(close)
                    signals = getattr(chart, method)()
                    _assert_signal_schema(self, signals, chart.matrix.shape[1])

                    used_types = signals["type"][signals["width"] != 0]
                    self.assertTrue(np.all(used_types >= 0))
                    self.assertTrue(np.all(used_types < len(SIGNAL_TYPES)))

    def test_legacy_buy_sell_pattern_helpers_initialize_breakouts(self) -> None:
        double_top = _close_chart([100, 103, 100, 103, 104])
        double_bottom = _close_chart([100, 97, 100, 97, 96])
        triple_top = _close_chart([100, 103, 100, 103, 100, 104])
        triple_bottom = _close_chart([100, 97, 100, 97, 100, 96])

        double_top.double_top_buy()
        double_bottom.double_bottom_sell()
        triple_top.triple_top_buy()
        triple_bottom.triple_bottom_sell()

        self.assertIn("DTB", double_top.buys)
        self.assertIn("DBS", double_bottom.sells)
        self.assertIn("TTB", triple_top.buys)
        self.assertIn("TBS", triple_bottom.sells)
        self.assertEqual(len(double_top.buys["DTB"]), len(double_top.pnf_timeseries["box index"]))
        self.assertEqual(len(double_bottom.sells["DBS"]), len(double_bottom.pnf_timeseries["box index"]))
        self.assertEqual(len(triple_top.buys["TTB"]), len(triple_top.pnf_timeseries["box index"]))
        self.assertEqual(len(triple_bottom.sells["TBS"]), len(triple_bottom.pnf_timeseries["box index"]))

    def test_next_simple_signal_returns_buy_sell_pair(self) -> None:
        next_buy, next_sell = _close_chart([100, 103, 100, 103, 104]).next_simple_signal()

        self.assertTrue(np.isnan(next_buy) or np.isfinite(next_buy))
        self.assertTrue(np.isnan(next_sell) or np.isfinite(next_sell))

    def test_get_signals_is_deterministic_for_same_input(self) -> None:
        first = _close_chart([100, 103, 100, 103, 100, 104]).get_signals()
        second = _close_chart([100, 103, 100, 103, 100, 104]).get_signals()

        for key in first:
            np.testing.assert_array_equal(first[key], second[key])

    def test_log_scaling_breakout_and_signal_calls_do_not_mutate_chart(self) -> None:
        chart = _close_chart([100, 103, 99.91, 104.03], scaling="log")
        matrix_before = chart.matrix.copy()
        boxscale_before = chart.boxscale.copy()

        chart.get_breakouts()
        chart.get_signals()

        np.testing.assert_array_equal(chart.matrix, matrix_before)
        np.testing.assert_array_equal(chart.boxscale, boxscale_before)


if __name__ == "__main__":
    unittest.main()
