import unittest

import numpy as np

from chart_pnf import PointFigureChart


def _filled_price_boxes(chart: PointFigureChart, column_index: int) -> np.ndarray:
    return chart.boxscale[np.where(chart.matrix[:, column_index] != 0)]


class ChartKnownExampleTests(unittest.TestCase):
    def test_close_method_first_x_column_example(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 101, 102, 103]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 1)
        np.testing.assert_allclose(_filled_price_boxes(chart, 0), np.array([101.0, 102.0, 103.0]))
        self.assertEqual(chart.pnf_timeseries["trend"][-1], 1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][-1], 3)

    def test_close_method_x_to_o_reversal_example(self) -> None:
        chart = PointFigureChart(
            ts={"close": [100, 103, 99.91]},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
        )

        self.assertEqual(chart.matrix.shape[1], 2)
        np.testing.assert_allclose(_filled_price_boxes(chart, 0), np.array([101.0, 102.0, 103.0]))
        np.testing.assert_allclose(_filled_price_boxes(chart, 1), np.array([99.91, 100.94, 101.97]))
        self.assertEqual(chart.pnf_timeseries["trend"][-1], -1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][-1], 3)

    def test_high_low_and_low_high_priority_examples(self) -> None:
        ts = {
            "high": [100, 103, 104.03],
            "low": [100, 103, 99.91],
        }

        high_first = PointFigureChart(ts=ts, method="h/l", reversal=3, boxsize=1, scaling="log")
        low_first = PointFigureChart(ts=ts, method="l/h", reversal=3, boxsize=1, scaling="log")

        self.assertEqual(high_first.matrix.shape[1], 1)
        np.testing.assert_allclose(_filled_price_boxes(high_first, 0), np.array([101.0, 102.0, 103.0, 104.03]))
        self.assertEqual(high_first.pnf_timeseries["trend"][-1], 1)
        self.assertEqual(high_first.pnf_timeseries["filled boxes"][-1], 4)

        self.assertEqual(low_first.matrix.shape[1], 2)
        np.testing.assert_allclose(_filled_price_boxes(low_first, 0), np.array([101.0, 102.0, 103.0]))
        np.testing.assert_allclose(_filled_price_boxes(low_first, 1), np.array([99.91, 100.94, 101.97]))
        self.assertEqual(low_first.pnf_timeseries["trend"][-1], -1)
        self.assertEqual(low_first.pnf_timeseries["filled boxes"][-1], 3)

    def test_hlc_close_confirm_then_high_fills_example(self) -> None:
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
        np.testing.assert_allclose(
            _filled_price_boxes(chart, 0),
            np.array([101.0, 102.0, 103.0, 104.03, 105.06]),
        )
        self.assertEqual(chart.pnf_timeseries["trend"][-1], 1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][-1], 5)

    def test_ohlc_bullish_candle_order_example(self) -> None:
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
        np.testing.assert_allclose(_filled_price_boxes(chart, 0), np.array([101.0, 102.0, 103.0]))
        np.testing.assert_allclose(_filled_price_boxes(chart, 1), np.array([99.91, 100.94, 101.97]))
        self.assertEqual(chart.pnf_timeseries["trend"][-1], -1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][-1], 3)

    def test_ohlc_bearish_candle_order_example(self) -> None:
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
        np.testing.assert_allclose(_filled_price_boxes(chart, 0), np.array([101.0, 102.0, 103.0, 104.03]))
        self.assertEqual(chart.pnf_timeseries["trend"][-1], 1)
        self.assertEqual(chart.pnf_timeseries["filled boxes"][-1], 4)


if __name__ == "__main__":
    unittest.main()
