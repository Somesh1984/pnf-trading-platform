from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .core import Column, PnFConfig
from .render import build_chart_grid


@dataclass(frozen=True)
class PriceLevel:
    kind: str
    price: Decimal
    box: int
    touches: int
    column_indices: tuple[int, ...]
    start_column: int
    end_column: int


def detect_horizontal_levels(
    columns: Iterable[Column],
    config: PnFConfig,
    min_touches: int = 3,
    cluster_threshold_boxes: int = 0,
) -> list[PriceLevel]:
    _require_config(config)
    if min_touches < 3:
        raise ValueError("min_touches must be greater than or equal to three")
    if cluster_threshold_boxes < 0:
        raise ValueError("cluster_threshold_boxes must be non-negative")
    column_list = list(columns)
    grid = build_chart_grid(column_list)
    resistance = _cluster_levels(
        [
            (grid.price_to_y[column.high], column.high, index)
            for index, column in enumerate(column_list)
            if column.type == "X"
        ],
        "resistance",
        min_touches,
        cluster_threshold_boxes,
    )
    support = _cluster_levels(
        [
            (grid.price_to_y[column.low], column.low, index)
            for index, column in enumerate(column_list)
            if column.type == "O"
        ],
        "support",
        min_touches,
        cluster_threshold_boxes,
    )
    return sorted(resistance + support, key=lambda level: (level.start_column, level.kind, level.box))


def _require_config(config: PnFConfig) -> None:
    if not isinstance(config, PnFConfig):
        raise TypeError("config must be a PnFConfig instance")
    _ = config.box_pct_decimal


def _cluster_levels(
    touches: list[tuple[int, Decimal, int]],
    kind: str,
    min_touches: int,
    threshold: int,
) -> list[PriceLevel]:
    if not touches:
        return []
    touches.sort(key=lambda item: (item[0], item[2]))
    clusters: list[list[tuple[int, Decimal, int]]] = []
    current: list[tuple[int, Decimal, int]] = [touches[0]]
    for touch in touches[1:]:
        if touch[0] - current[-1][0] <= threshold:
            current.append(touch)
        else:
            clusters.append(current)
            current = [touch]
    clusters.append(current)

    levels: list[PriceLevel] = []
    for cluster in clusters:
        if len(cluster) < min_touches:
            continue
        boxes = [item[0] for item in cluster]
        prices = [item[1] for item in cluster]
        indices = tuple(item[2] for item in cluster)
        middle = len(prices) // 2
        sorted_prices = sorted(prices)
        sorted_boxes = sorted(boxes)
        levels.append(
            PriceLevel(
                kind=kind,
                price=sorted_prices[middle],
                box=sorted_boxes[middle],
                touches=len(cluster),
                column_indices=indices,
                start_column=min(indices),
                end_column=max(indices),
            )
        )
    return levels
