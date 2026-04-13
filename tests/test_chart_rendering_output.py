from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import unittest

import matplotlib

matplotlib.use("Agg", force=True)
from matplotlib import pyplot as plt
import numpy as np

from chart_pnf import PointFigureChart


LOG_CLOSE = [100, 101, 102, 103, 100, 99, 98, 101, 104]


def _render_chart(chart: PointFigureChart) -> tuple[str, str]:
    output = StringIO()
    with redirect_stdout(output):
        result = str(chart)
    return result, output.getvalue()


class ChartRenderingOutputTests(unittest.TestCase):
    def test_log_chart_text_render_is_deterministic_and_read_only(self) -> None:
        chart = PointFigureChart(
            ts={"close": LOG_CLOSE},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
            title="Render Smoke",
        )
        matrix_before = chart.matrix.copy()
        boxscale_before = chart.boxscale.copy()

        first_result, first_output = _render_chart(chart)
        second_result, second_output = _render_chart(chart)

        self.assertEqual(first_result, "printed 3/3 columns.")
        self.assertEqual(first_result, second_result)
        self.assertEqual(first_output, second_output)
        self.assertIn("Point & Figure (log|cl) 1% x 3 | Render Smoke", first_output)
        self.assertIn("X", first_output)
        self.assertIn("O", first_output)
        self.assertIn(".", first_output)
        self.assertIn("103.86", first_output)
        np.testing.assert_array_equal(chart.matrix, matrix_before)
        np.testing.assert_array_equal(chart.boxscale, boxscale_before)

    def test_print_columns_limits_rendered_chart_to_last_columns(self) -> None:
        chart = PointFigureChart(
            ts={"close": LOG_CLOSE},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
        )
        chart.print_columns = 2

        result, output = _render_chart(chart)

        self.assertEqual(result, "printed 2/3 columns.")
        rendered_rows = [line for line in output.splitlines() if line and line[0].isdigit()]
        self.assertTrue(rendered_rows)
        for row in rendered_rows:
            self.assertLessEqual(len(row.split()), 4)

    def test_ohlc_log_chart_text_render_is_crash_free(self) -> None:
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

        result, output = _render_chart(chart)

        self.assertEqual(result, "printed 2/2 columns.")
        self.assertIn("Point & Figure (log|ohlc) 1% x 3", output)
        self.assertIn("X", output)
        self.assertIn("O", output)

    def test_log_plot_assembly_is_crash_free_and_read_only(self) -> None:
        chart = PointFigureChart(
            ts={"close": LOG_CLOSE},
            method="cl",
            reversal=3,
            boxsize=1,
            scaling="log",
            title="Plot Smoke",
        )
        matrix_before = chart.matrix.copy()
        boxscale_before = chart.boxscale.copy()

        chart._assemble_plot_chart()
        assert chart.fig is not None
        chart.fig.canvas.draw()

        self.assertIsNotNone(chart.fig)
        self.assertIsNotNone(chart.ax2)
        self.assertGreater(chart.plot_matrix.size, 0)
        self.assertGreater(chart.plot_boxscale.size, 0)
        np.testing.assert_array_equal(chart.matrix, matrix_before)
        np.testing.assert_array_equal(chart.boxscale, boxscale_before)
        plt.close(chart.fig)
