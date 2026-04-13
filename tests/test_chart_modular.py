import inspect
import unittest

import numpy as np
import chart_pnf.chart_engine as chart_engine_module

from chart_pnf import (
    ChartCountMixin,
    ChartEngineMixin,
    ChartIndicatorMixin,
    ChartPatternMixin,
    ChartPlottingMixin,
    ChartRenderingMixin,
    ChartSetupMixin,
    ChartSignalMixin,
    PointFigureChart,
)


class ChartModularTests(unittest.TestCase):
    def test_public_chart_entrypoint_keeps_legacy_api(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 101, 102, 103, 100, 99, 98, 101, 104]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="abs",
            title="Smoke",
        )

        self.assertEqual(chart.matrix.shape, (47, 3))
        self.assertIn("Point & Figure (abs|cl) 1 x 3", chart.title)
        self.assertTrue(callable(chart.get_breakouts))
        self.assertTrue(callable(chart.get_trendlines))
        self.assertTrue(callable(chart.sma))
        self.assertTrue(callable(chart.get_counts))
        self.assertTrue(callable(chart.show))

    def test_chart_class_is_composed_from_single_responsibility_mixins(self) -> None:
        expected_mixins = (
            ChartSetupMixin,
            ChartEngineMixin,
            ChartPatternMixin,
            ChartIndicatorMixin,
            ChartSignalMixin,
            ChartCountMixin,
            ChartPlottingMixin,
            ChartRenderingMixin,
        )

        for mixin in expected_mixins:
            self.assertTrue(issubclass(PointFigureChart, mixin))

    def test_chart_engine_does_not_depend_on_pnf_core(self) -> None:
        self.assertNotIn("pnf.core", inspect.getsource(chart_engine_module))

    def test_log_scaling_uses_step_frozen_percentage_boxes_for_close_method(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 103, 107.12]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        filled_boxes = chart.boxscale[np.where(chart.matrix[:, 0] == 1)]

        np.testing.assert_allclose(
            filled_boxes,
            np.array([101.0, 102.0, 103.0, 104.03, 105.06, 106.09, 107.12]),
        )

    def test_log_compounding_scaling_keeps_legacy_global_log_grid(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 103, 107.12]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log_compounding",
        )

        filled_boxes = chart.boxscale[np.where(chart.matrix[:, 0] == 1)]

        self.assertIn("Point & Figure (log_compounding|cl) 1% x 3", chart.title)
        self.assertGreater(len(filled_boxes), 0)
        self.assertFalse(
            np.allclose(
                filled_boxes[: min(len(filled_boxes), 7)],
                np.array([101.0, 102.0, 103.0, 104.03, 105.06, 106.09, 107.12])[: min(len(filled_boxes), 7)],
            )
        )

    def test_log_scaling_initial_column_requires_reversal_move(self) -> None:
        with self.assertRaises(ValueError):
            PointFigureChart(
                ts={"close": [100, 101]},
                method="cl",
                reversal=3,
                boxsize=1,
                scaling="log",
            )

    def test_log_scaling_supports_high_low_reversal(self) -> None:
        chart = PointFigureChart(
            ts={
                "high": [100, 103, 102],
                "low": [100, 103, 99.91],
            },
            method="h/l",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 2)
        self.assertEqual(chart.pnf_timeseries["trend"][1], 1)
        self.assertEqual(chart.pnf_timeseries["trend"][2], -1)

    def test_log_scaling_high_low_method_uses_high_before_low(self) -> None:
        chart = PointFigureChart(
            ts={
                "high": [100, 103, 104.03],
                "low": [100, 103, 99.91],
            },
            method="h/l",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 1)
        self.assertEqual(chart.pnf_timeseries["trend"][2], 1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][2], 4)

    def test_log_scaling_low_high_method_uses_low_before_high(self) -> None:
        chart = PointFigureChart(
            ts={
                "high": [100, 103, 104.03],
                "low": [100, 103, 99.91],
            },
            method="l/h",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 2)
        self.assertEqual(chart.pnf_timeseries["trend"][2], -1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][2], 3)

    def test_log_scaling_hlc_requires_close_to_confirm_extension(self) -> None:
        chart = PointFigureChart(
            ts={
                "high": [100, 103, 104.03],
                "low": [100, 103, 100],
                "close": [100, 103, 103.50],
            },
            method="hlc",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 1)
        self.assertEqual(np.count_nonzero(chart.matrix[:, 0]), 3)

    def test_log_scaling_hlc_uses_high_after_close_confirms_extension(self) -> None:
        chart = PointFigureChart(
            ts={
                "high": [100, 103, 105.06],
                "low": [100, 103, 100],
                "close": [100, 103, 104.03],
            },
            method="hlc",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 1)
        self.assertEqual(np.count_nonzero(chart.matrix[:, 0]), 5)

    def test_log_scaling_hlc_requires_close_to_confirm_reversal(self) -> None:
        chart = PointFigureChart(
            ts={
                "high": [100, 103, 103],
                "low": [100, 103, 99.91],
                "close": [100, 103, 101],
            },
            method="hlc",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 1)
        self.assertEqual(np.count_nonzero(chart.matrix[:, 0]), 3)

    def test_log_scaling_hlc_uses_low_after_close_confirms_reversal(self) -> None:
        chart = PointFigureChart(
            ts={
                "high": [100, 103, 103],
                "low": [100, 103, 98.88],
                "close": [100, 103, 99.91],
            },
            method="hlc",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 2)
        self.assertEqual(np.count_nonzero(chart.matrix[:, 1]), 4)
        self.assertEqual(chart.pnf_timeseries["trend"][2], -1)

    def test_log_scaling_ohlc_supports_existing_bullish_candle_order(self) -> None:
        chart = PointFigureChart(
            ts={
                "open": [100, 100, 103],
                "high": [100, 103, 104.03],
                "low": [100, 100, 99.91],
                "close": [100, 103, 104],
            },
            method="ohlc",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 2)
        self.assertEqual(chart.pnf_timeseries["trend"][2], -1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][2], 3)

    def test_log_scaling_ohlc_supports_existing_bearish_candle_order(self) -> None:
        chart = PointFigureChart(
            ts={
                "open": [100, 100, 104],
                "high": [100, 103, 104.03],
                "low": [100, 100, 99.91],
                "close": [100, 103, 100],
            },
            method="ohlc",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 1)
        self.assertEqual(chart.pnf_timeseries["trend"][2], 1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][2], 4)

    def test_log_scaling_ohlc_is_deterministic(self) -> None:
        ts = {
            "open": [100, 100, 103],
            "high": [100, 103, 104.03],
            "low": [100, 100, 99.91],
            "close": [100, 103, 104],
        }
        first = PointFigureChart(ts=ts, method="ohlc", reversal=3, boxsize=1, scaling="log")
        second = PointFigureChart(ts=ts, method="ohlc", reversal=3, boxsize=1, scaling="log")

        np.testing.assert_array_equal(first.matrix, second.matrix)
        np.testing.assert_array_equal(first.pnf_timeseries["trend"], second.pnf_timeseries["trend"])

    def test_log_scaling_large_gap_up_creates_multiple_x_boxes(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 107]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 1)
        self.assertEqual(np.count_nonzero(chart.matrix[:, 0]), 7)
        self.assertEqual(chart.pnf_timeseries["trend"][1], 1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][1], 7)

    def test_log_scaling_large_gap_down_creates_multiple_o_boxes(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 92]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 1)
        self.assertEqual(np.count_nonzero(chart.matrix[:, 0]), 8)
        self.assertEqual(chart.pnf_timeseries["trend"][1], -1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][1], 8)

    def test_log_scaling_exact_reversal_threshold_creates_reversal(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 103, 99.91]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 2)
        self.assertEqual(np.count_nonzero(chart.matrix[:, 1]), 3)
        self.assertEqual(chart.pnf_timeseries["trend"][2], -1)

    def test_log_scaling_move_below_reversal_threshold_does_not_reverse(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 103, 99.92]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 1)
        self.assertEqual(np.count_nonzero(chart.matrix[:, 0]), 3)

    def test_log_scaling_x_to_o_reversal_works(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 103, 99.91]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.pnf_timeseries["trend"][1], 1)
        self.assertEqual(chart.pnf_timeseries["trend"][2], -1)

    def test_log_scaling_o_to_x_reversal_works(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 97, 99.91]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 2)
        self.assertEqual(chart.pnf_timeseries["trend"][1], -1)
        self.assertEqual(chart.pnf_timeseries["trend"][2], 1)

    def test_log_scaling_gap_and_reversal_cases_are_deterministic(self) -> None:
        ts = {"close": [100, 107, 99.51, 105.48, 98.15]}
        first = PointFigureChart(ts=ts, method="cl", reversal=3, boxsize=1, scaling="log")
        second = PointFigureChart(ts=ts, method="cl", reversal=3, boxsize=1, scaling="log")

        np.testing.assert_array_equal(first.matrix, second.matrix)
        np.testing.assert_array_equal(first.pnf_timeseries["trend"], second.pnf_timeseries["trend"])


if __name__ == "__main__":
    unittest.main()
