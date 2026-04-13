from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, TypedDict

from .core import Column
from .utils import decimal_to_string


@dataclass(frozen=True)
class ChartGrid:
    prices: tuple[Decimal, ...]
    price_to_y: dict[Decimal, int]


class ColumnTableRow(TypedDict):
    type: str
    box_count: int
    high: Decimal
    low: Decimal
    start_index: int
    end_index: int


class ChartRow(TypedDict):
    price: Decimal
    cells: list[str]


def build_chart_grid(columns: Iterable[Column]) -> ChartGrid:
    prices = tuple(sorted({box for column in columns for box in _column_boxes(column)}))
    return ChartGrid(prices=prices, price_to_y={price: index for index, price in enumerate(prices)})


def columns_to_table(columns: Iterable[Column]) -> list[ColumnTableRow]:
    return [
        {
            "type": column.type,
            "box_count": column.box_count,
            "high": column.high,
            "low": column.low,
            "start_index": column.start_index,
            "end_index": column.end_index,
        }
        for column in columns
    ]


def columns_to_rows(columns: Iterable[Column]) -> list[ChartRow]:
    column_list = list(columns)
    grid = build_chart_grid(column_list)
    column_boxes = [set(_column_boxes(column)) for column in column_list]
    rows: list[ChartRow] = []
    for price in reversed(grid.prices):
        cells: list[str] = []
        for column, boxes in zip(column_list, column_boxes):
            cells.append(column.type if price in boxes else "")
        rows.append({"price": price, "cells": cells})
    return rows


def render_ascii_chart(columns: Iterable[Column]) -> str:
    column_list = list(columns)
    if not column_list:
        return ""
    rows = columns_to_rows(column_list)
    price_width = max(len(decimal_to_string(row["price"])) for row in rows)
    header = " " * (price_width + 1) + " ".join(str(index) for index in range(len(column_list)))
    lines = [header]
    for row in rows:
        price = decimal_to_string(row["price"])
        cells = [cell or "." for cell in row["cells"]]
        lines.append(f"{price.rjust(price_width)} " + " ".join(cells))
    return "\n".join(lines)


def _column_boxes(column: Column) -> tuple[Decimal, ...]:
    if column.boxes:
        return column.boxes
    return (column.high,) if column.high == column.low else (column.low, column.high)
