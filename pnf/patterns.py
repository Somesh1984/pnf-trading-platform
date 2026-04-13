from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from .core import Column, PnFConfig


@dataclass(frozen=True)
class PatternSignal:
    name: str
    direction: str
    column_index: int
    level: Decimal
    breakout: Decimal
    confirmed_by: tuple[int, ...]


def detect_patterns(columns: Iterable[Column], config: PnFConfig) -> list[PatternSignal]:
    _require_config(config)
    column_list = list(columns)
    signals: list[PatternSignal] = []
    signals.extend(detect_double_top_breakouts(column_list, config))
    signals.extend(detect_double_bottom_breakdowns(column_list, config))
    signals.extend(detect_triple_top_breakouts(column_list, config))
    signals.extend(detect_triple_bottom_breakdowns(column_list, config))
    signals.extend(detect_bullish_catapults(column_list, config))
    signals.extend(detect_bearish_catapults(column_list, config))
    return sorted(signals, key=lambda signal: (signal.column_index, signal.name))


def detect_double_top_breakouts(columns: Iterable[Column], config: PnFConfig) -> list[PatternSignal]:
    _require_config(config)
    column_list = list(columns)
    signals: list[PatternSignal] = []
    for index in range(2, len(column_list)):
        left, middle, current = column_list[index - 2], column_list[index - 1], column_list[index]
        if left.type == "X" and middle.type == "O" and current.type == "X" and current.high > left.high:
            signals.append(
                PatternSignal(
                    name="double_top_breakout",
                    direction="bullish",
                    column_index=index,
                    level=left.high,
                    breakout=current.high,
                    confirmed_by=(index - 2, index - 1),
                )
            )
    return signals


def detect_double_bottom_breakdowns(columns: Iterable[Column], config: PnFConfig) -> list[PatternSignal]:
    _require_config(config)
    column_list = list(columns)
    signals: list[PatternSignal] = []
    for index in range(2, len(column_list)):
        left, middle, current = column_list[index - 2], column_list[index - 1], column_list[index]
        if left.type == "O" and middle.type == "X" and current.type == "O" and current.low < left.low:
            signals.append(
                PatternSignal(
                    name="double_bottom_breakdown",
                    direction="bearish",
                    column_index=index,
                    level=left.low,
                    breakout=current.low,
                    confirmed_by=(index - 2, index - 1),
                )
            )
    return signals


def detect_triple_top_breakouts(columns: Iterable[Column], config: PnFConfig) -> list[PatternSignal]:
    _require_config(config)
    column_list = list(columns)
    signals: list[PatternSignal] = []
    for index in range(4, len(column_list)):
        c0, c1, c2, c3, current = column_list[index - 4 : index + 1]
        if (
            c0.type == "X"
            and c1.type == "O"
            and c2.type == "X"
            and c3.type == "O"
            and current.type == "X"
            and c0.high == c2.high
            and current.high > c0.high
        ):
            signals.append(
                PatternSignal(
                    name="triple_top_breakout",
                    direction="bullish",
                    column_index=index,
                    level=c0.high,
                    breakout=current.high,
                    confirmed_by=(index - 4, index - 2, index - 1),
                )
            )
    return signals


def detect_triple_bottom_breakdowns(columns: Iterable[Column], config: PnFConfig) -> list[PatternSignal]:
    _require_config(config)
    column_list = list(columns)
    signals: list[PatternSignal] = []
    for index in range(4, len(column_list)):
        c0, c1, c2, c3, current = column_list[index - 4 : index + 1]
        if (
            c0.type == "O"
            and c1.type == "X"
            and c2.type == "O"
            and c3.type == "X"
            and current.type == "O"
            and c0.low == c2.low
            and current.low < c0.low
        ):
            signals.append(
                PatternSignal(
                    name="triple_bottom_breakdown",
                    direction="bearish",
                    column_index=index,
                    level=c0.low,
                    breakout=current.low,
                    confirmed_by=(index - 4, index - 2, index - 1),
                )
            )
    return signals


def detect_bullish_catapults(columns: Iterable[Column], config: PnFConfig) -> list[PatternSignal]:
    _require_config(config)
    column_list = list(columns)
    signals: list[PatternSignal] = []
    for index in range(4, len(column_list)):
        c0, c1, c2, c3, current = column_list[index - 4 : index + 1]
        if (
            c0.type == "X"
            and c1.type == "O"
            and c2.type == "X"
            and c3.type == "O"
            and current.type == "X"
            and c2.high > c0.high
            and c3.low > c1.low
            and current.high > c2.high
        ):
            signals.append(
                PatternSignal(
                    name="bullish_catapult",
                    direction="bullish",
                    column_index=index,
                    level=c2.high,
                    breakout=current.high,
                    confirmed_by=(index - 4, index - 2, index - 1),
                )
            )
    return signals


def detect_bearish_catapults(columns: Iterable[Column], config: PnFConfig) -> list[PatternSignal]:
    _require_config(config)
    column_list = list(columns)
    signals: list[PatternSignal] = []
    for index in range(4, len(column_list)):
        c0, c1, c2, c3, current = column_list[index - 4 : index + 1]
        if (
            c0.type == "O"
            and c1.type == "X"
            and c2.type == "O"
            and c3.type == "X"
            and current.type == "O"
            and c2.low < c0.low
            and c3.high < c1.high
            and current.low < c2.low
        ):
            signals.append(
                PatternSignal(
                    name="bearish_catapult",
                    direction="bearish",
                    column_index=index,
                    level=c2.low,
                    breakout=current.low,
                    confirmed_by=(index - 4, index - 2, index - 1),
                )
            )
    return signals


def _require_config(config: PnFConfig) -> None:
    if not isinstance(config, PnFConfig):
        raise TypeError("config must be a PnFConfig instance")
    _ = config.box_pct_decimal
