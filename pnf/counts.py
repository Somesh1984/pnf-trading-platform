from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .core import Column, PnFConfig, calculate_logscale_box_size, calculate_step_box_size
from .patterns import PatternSignal, detect_patterns
from .utils import decimal_add, decimal_mul_int, decimal_round_nearest, decimal_sub


@dataclass(frozen=True)
class CountTarget:
    kind: str
    direction: str
    start_column: int
    end_column: int
    count: int
    box_size: Decimal
    base_price: Decimal
    target: Decimal


def horizontal_count(
    columns: Iterable[Column],
    config: PnFConfig,
    start_column: int,
    end_column: int,
    direction: str,
) -> CountTarget:
    column_list = list(columns)
    if direction not in {"bullish", "bearish"}:
        raise ValueError('direction must be "bullish" or "bearish"')
    if start_column < 0 or end_column >= len(column_list) or start_column > end_column:
        raise ValueError("invalid horizontal count column range")
    count = end_column - start_column + 1
    base_column = column_list[end_column]
    base_price = base_column.high if direction == "bullish" else base_column.low
    box_size, target = _project_target(base_price, count * config.reversal, direction, config)
    return CountTarget(
        kind="horizontal",
        direction=direction,
        start_column=start_column,
        end_column=end_column,
        count=count,
        box_size=box_size,
        base_price=base_price,
        target=target,
    )


def vertical_count(
    columns: Iterable[Column],
    config: PnFConfig,
    patterns: Iterable[PatternSignal] | None = None,
    direction: str | None = None,
) -> CountTarget | None:
    column_list = list(columns)
    pattern_list = list(patterns) if patterns is not None else detect_patterns(column_list, config)
    if direction is not None and direction not in {"bullish", "bearish"}:
        raise ValueError('direction must be "bullish", "bearish", or None')
    for pattern in sorted(pattern_list, key=lambda item: item.column_index):
        if direction is not None and pattern.direction != direction:
            continue
        column = column_list[pattern.column_index]
        base_price = column.high if pattern.direction == "bullish" else column.low
        box_size, target = _project_target(base_price, column.box_count * config.reversal, pattern.direction, config)
        return CountTarget(
            kind="vertical",
            direction=pattern.direction,
            start_column=pattern.column_index,
            end_column=pattern.column_index,
            count=column.box_count,
            box_size=box_size,
            base_price=base_price,
            target=target,
        )
    return None


def _project_target(
    base_price: Decimal,
    box_steps: int,
    direction: str,
    config: PnFConfig,
) -> tuple[Decimal, Decimal]:
    if config.scaling == "step_box":
        box_size = calculate_step_box_size(base_price, config)
        distance = decimal_mul_int(box_size, box_steps)
        raw_target = decimal_add(base_price, distance) if direction == "bullish" else decimal_sub(base_price, distance)
        return box_size, decimal_round_nearest(raw_target, config.tick_size_decimal)

    box_size = calculate_logscale_box_size(base_price, config)
    target = base_price
    for _ in range(box_steps):
        current_box_size = calculate_logscale_box_size(target, config)
        raw_target = decimal_add(target, current_box_size) if direction == "bullish" else decimal_sub(target, current_box_size)
        target = decimal_round_nearest(raw_target, config.tick_size_decimal)
    return box_size, target
