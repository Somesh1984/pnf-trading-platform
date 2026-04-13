import unittest

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


if __name__ == "__main__":
    unittest.main()
