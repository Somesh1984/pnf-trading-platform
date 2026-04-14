from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import unittest
from typing import Any

import numpy as np

from chart_pnf import PointFigureChart
from pnf.core import Column, PnFConfig, build_columns


CENT = Decimal("0.01")


@dataclass(frozen=True)
class NormalizedColumn:
    type: str
    boxes: tuple[Decimal, ...]
    low: Decimal
    high: Decimal
    box_count: int


def _to_cent(value: Any) -> Decimal:
    return Decimal(str(value)).quantize(CENT)


def _normalized_chart_columns(chart: PointFigureChart) -> tuple[NormalizedColumn, ...]:
    columns: list[NormalizedColumn] = []
    for column_index in range(chart.matrix.shape[1]):
        values = chart.boxscale[np.where(chart.matrix[:, column_index] != 0)]
        boxes = tuple(sorted(_to_cent(value) for value in values))
        column_type = "X" if np.any(chart.matrix[:, column_index] > 0) else "O"
        columns.append(
            NormalizedColumn(
                type=column_type,
                boxes=boxes,
                low=boxes[0],
                high=boxes[-1],
                box_count=len(boxes),
            )
        )
    return tuple(columns)


def _normalized_core_columns(columns: list[Column]) -> tuple[NormalizedColumn, ...]:
    normalized: list[NormalizedColumn] = []
    for column in columns:
        boxes = tuple(sorted(_to_cent(value) for value in column.boxes))
        normalized.append(
            NormalizedColumn(
                type=column.type,
                boxes=boxes,
                low=_to_cent(column.low),
                high=_to_cent(column.high),
                box_count=column.box_count,
            )
        )
    return tuple(normalized)


def _compare_close(close: list[float]) -> tuple[NormalizedColumn, ...]:
    chart = PointFigureChart(ts={"close": close}, method="cl", reversal=3, boxsize=1, scaling="log")
    core = build_columns(close, PnFConfig(box_pct=0.01, reversal=3, method="close"))

    chart_columns = _normalized_chart_columns(chart)
    core_columns = _normalized_core_columns(core)

    assert chart_columns == core_columns
    return chart_columns


def _compare_high_low(rows: list[dict[str, float]]) -> tuple[NormalizedColumn, ...]:
    chart = PointFigureChart(
        ts={
            "high": [row["high"] for row in rows],
            "low": [row["low"] for row in rows],
        },
        method="h/l",
        reversal=3,
        boxsize=1,
        scaling="log",
    )
    core = build_columns(rows, PnFConfig(box_pct=0.01, reversal=3, method="high_low"))

    chart_columns = _normalized_chart_columns(chart)
    core_columns = _normalized_core_columns(core)

    assert chart_columns == core_columns
    return chart_columns


class ChartPnfCoreComparisonTests(unittest.TestCase):
    def test_close_first_x_column_matches_core(self) -> None:
        columns = _compare_close([100, 103])

        self.assertEqual(
            columns,
            (
                NormalizedColumn("X", (Decimal("101.00"), Decimal("102.00"), Decimal("103.00")), Decimal("101.00"), Decimal("103.00"), 3),
            ),
        )

    def test_close_x_extension_matches_core(self) -> None:
        columns = _compare_close([100, 103, 107.12])

        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].type, "X")
        self.assertEqual(columns[0].box_count, 7)
        self.assertEqual(columns[0].high, Decimal("107.12"))

    def test_close_x_to_o_reversal_matches_core_after_box_order_normalization(self) -> None:
        columns = _compare_close([100, 103, 99.91])

        self.assertEqual([column.type for column in columns], ["X", "O"])
        self.assertEqual(columns[1].boxes, (Decimal("99.91"), Decimal("100.94"), Decimal("101.97")))

    def test_close_large_gap_matches_core(self) -> None:
        columns = _compare_close([100, 110])

        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].type, "X")
        self.assertEqual(columns[0].box_count, 10)
        self.assertEqual(columns[0].high, Decimal("110.00"))

    def test_high_low_extension_priority_matches_core(self) -> None:
        rows = [
            {"high": 100, "low": 100},
            {"high": 103, "low": 103},
            {"high": 104.03, "low": 99.91},
        ]

        columns = _compare_high_low(rows)

        self.assertEqual(len(columns), 1)
        self.assertEqual(columns[0].type, "X")
        self.assertEqual(columns[0].boxes[-1], Decimal("104.03"))

    def test_high_low_reversal_matches_core_when_no_extension_occurs(self) -> None:
        rows = [
            {"high": 100, "low": 100},
            {"high": 103, "low": 103},
            {"high": 102, "low": 99.91},
        ]

        columns = _compare_high_low(rows)

        self.assertEqual([column.type for column in columns], ["X", "O"])
        self.assertEqual(columns[1].low, Decimal("99.91"))

    def test_comparison_output_is_deterministic(self) -> None:
        first = _compare_close([100, 103, 99.91])
        second = _compare_close([100, 103, 99.91])

        self.assertEqual(first, second)
