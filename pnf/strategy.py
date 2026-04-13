from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .core import Column, PnFConfig
from .counts import CountTarget, horizontal_count, vertical_count
from .levels import PriceLevel, detect_horizontal_levels
from .patterns import PatternSignal, detect_patterns
from .trendlines import bearish_resistance_line, bullish_support_line


@dataclass(frozen=True)
class TradeSignal:
    direction: str
    entry: Decimal
    stop_loss: Decimal
    target: Decimal
    pattern_name: str
    column_index: int
    count_kind: str


def generate_trades(
    columns: Iterable[Column],
    config: PnFConfig,
    patterns: Iterable[PatternSignal] | None = None,
    levels: Iterable[PriceLevel] | None = None,
    counts: Iterable[CountTarget] | None = None,
) -> list[TradeSignal]:
    column_list = list(columns)
    pattern_list = list(patterns) if patterns is not None else detect_patterns(column_list, config)
    level_list = list(levels) if levels is not None else detect_horizontal_levels(column_list, config)
    count_list = list(counts) if counts is not None else _default_counts(column_list, config, pattern_list, level_list)
    bullish_line = bullish_support_line(column_list, config)
    bearish_line = bearish_resistance_line(column_list, config)
    trades: list[TradeSignal] = []
    used_directions: set[str] = set()
    for pattern in sorted(pattern_list, key=lambda item: item.column_index):
        if pattern.direction in used_directions:
            continue
        if pattern.direction == "bullish" and bullish_line is not None and bullish_line.broken_at is not None:
            if bullish_line.broken_at <= pattern.column_index:
                continue
        if pattern.direction == "bearish" and bearish_line is not None and bearish_line.broken_at is not None:
            if bearish_line.broken_at <= pattern.column_index:
                continue
        stop = _stop_loss(column_list, pattern)
        if stop is None:
            continue
        count = _matching_count(count_list, pattern)
        if count is None:
            continue
        trades.append(
            TradeSignal(
                direction=pattern.direction,
                entry=pattern.breakout,
                stop_loss=stop,
                target=count.target,
                pattern_name=pattern.name,
                column_index=pattern.column_index,
                count_kind=count.kind,
            )
        )
        used_directions.add(pattern.direction)
    return trades


def _default_counts(
    columns: list[Column],
    config: PnFConfig,
    patterns: list[PatternSignal],
    levels: list[PriceLevel],
) -> list[CountTarget]:
    targets: list[CountTarget] = []
    bullish_vertical = vertical_count(columns, config, patterns, "bullish")
    bearish_vertical = vertical_count(columns, config, patterns, "bearish")
    if bullish_vertical is not None:
        targets.append(bullish_vertical)
    if bearish_vertical is not None:
        targets.append(bearish_vertical)
    for level in levels:
        direction = "bullish" if level.kind == "resistance" else "bearish"
        targets.append(horizontal_count(columns, config, level.start_column, level.end_column, direction))
    return targets


def _matching_count(counts: list[CountTarget], pattern: PatternSignal) -> CountTarget | None:
    candidates = [
        count
        for count in counts
        if count.direction == pattern.direction and count.end_column <= pattern.column_index
    ]
    if not candidates:
        candidates = [count for count in counts if count.direction == pattern.direction]
    if not candidates:
        return None
    return sorted(candidates, key=lambda item: (item.kind != "vertical", item.end_column))[0]


def _stop_loss(columns: list[Column], pattern: PatternSignal) -> Decimal | None:
    prior = columns[: pattern.column_index]
    if pattern.direction == "bullish":
        lows = [column.low for column in reversed(prior) if column.type == "O"]
        return lows[0] if lows else None
    highs = [column.high for column in reversed(prior) if column.type == "X"]
    return highs[0] if highs else None
