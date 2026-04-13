from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .core import Column, PnFConfig
from .render import build_chart_grid


@dataclass(frozen=True)
class Trendline:
    kind: str
    anchor_column: int
    anchor_box: int
    slope: int
    broken_at: int | None = None

    def box_at(self, column_index: int) -> int:
        return self.anchor_box + self.slope * (column_index - self.anchor_column)


def bullish_support_line(columns: Iterable[Column], config: PnFConfig) -> Trendline | None:
    _require_config(config)
    column_list = list(columns)
    grid = build_chart_grid(column_list)
    candidates = [
        (index, grid.price_to_y[column.low])
        for index, column in enumerate(column_list)
        if column.type == "O" and column.low in grid.price_to_y
    ]
    if not candidates:
        return None
    anchor_column, anchor_box = min(candidates, key=lambda item: (item[1], item[0]))
    line = Trendline(kind="bullish_support", anchor_column=anchor_column, anchor_box=anchor_box, slope=1)
    return _with_break(column_list, grid.price_to_y, line)


def bearish_resistance_line(columns: Iterable[Column], config: PnFConfig) -> Trendline | None:
    _require_config(config)
    column_list = list(columns)
    grid = build_chart_grid(column_list)
    candidates = [
        (index, grid.price_to_y[column.high])
        for index, column in enumerate(column_list)
        if column.type == "X" and column.high in grid.price_to_y
    ]
    if not candidates:
        return None
    anchor_column, anchor_box = max(candidates, key=lambda item: (item[1], -item[0]))
    line = Trendline(kind="bearish_resistance", anchor_column=anchor_column, anchor_box=anchor_box, slope=-1)
    return _with_break(column_list, grid.price_to_y, line)


def is_line_broken(line: Trendline) -> bool:
    return line.broken_at is not None


def _require_config(config: PnFConfig) -> None:
    if not isinstance(config, PnFConfig):
        raise TypeError("config must be a PnFConfig instance")
    _ = config.box_pct_decimal


def _with_break(columns: list[Column], price_to_y: dict, line: Trendline) -> Trendline:
    broken_at: int | None = None
    for index, column in enumerate(columns[line.anchor_column + 1 :], start=line.anchor_column + 1):
        expected_box = line.box_at(index)
        if line.kind == "bullish_support":
            low_box = price_to_y[column.low]
            if low_box < expected_box:
                broken_at = index
                break
        else:
            high_box = price_to_y[column.high]
            if high_box > expected_box:
                broken_at = index
                break
    if broken_at is None:
        return line
    return Trendline(
        kind=line.kind,
        anchor_column=line.anchor_column,
        anchor_box=line.anchor_box,
        slope=line.slope,
        broken_at=broken_at,
    )
