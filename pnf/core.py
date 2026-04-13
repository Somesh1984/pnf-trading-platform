from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Iterable, Iterator, Sequence

from .utils import (
    decimal_add,
    decimal_div_floor,
    decimal_mul,
    decimal_mul_int,
    decimal_round_nearest,
    decimal_sub,
    require_positive_price,
    to_decimal,
)


@dataclass(frozen=True)
class PnFConfig:
    box_pct: float
    reversal: int
    method: str = "close"
    scaling: str = "step_box"
    tick_size: Decimal | float | str = Decimal("0.01")

    def __post_init__(self) -> None:
        box_pct = to_decimal(self.box_pct)
        if box_pct is None or box_pct <= 0:
            raise ValueError("box_pct must be greater than zero")
        if not isinstance(self.reversal, int) or self.reversal < 1:
            raise ValueError("reversal must be an integer greater than or equal to one")
        if self.method not in {"close", "high_low", "high_low_close"}:
            raise ValueError('method must be "close", "high_low", or "high_low_close"')
        if self.scaling not in {"step_box", "log"}:
            raise ValueError('scaling must be "step_box" or "log"')
        tick_size = to_decimal(self.tick_size)
        if tick_size is None or tick_size <= 0:
            raise ValueError("tick_size must be greater than zero")

    @property
    def box_pct_decimal(self) -> Decimal:
        box_pct = to_decimal(self.box_pct)
        if box_pct is None:
            raise ValueError("box_pct must be a finite decimal value")
        return box_pct

    @property
    def tick_size_decimal(self) -> Decimal:
        tick_size = to_decimal(self.tick_size)
        if tick_size is None or tick_size <= 0:
            raise ValueError("tick_size must be a finite positive decimal value")
        return tick_size


@dataclass(frozen=True)
class Column:
    type: str
    box_count: int
    high: Decimal
    low: Decimal
    start_index: int
    end_index: int
    boxes: tuple[Decimal, ...] = field(default_factory=tuple, repr=False)

    def __post_init__(self) -> None:
        if self.type not in {"X", "O"}:
            raise ValueError('column type must be "X" or "O"')
        if self.box_count < 1:
            raise ValueError("box_count must be greater than zero")
        if self.high < self.low:
            raise ValueError("column high must be greater than or equal to low")
        if self.start_index > self.end_index:
            raise ValueError("start_index must be less than or equal to end_index")
        if self.boxes and len(self.boxes) != self.box_count:
            raise ValueError("box_count must match boxes length")

    @property
    def last_box(self) -> Decimal:
        return self.high if self.type == "X" else self.low


@dataclass(frozen=True)
class PriceUpdate:
    index: int
    close: Decimal | None = None
    high: Decimal | None = None
    low: Decimal | None = None


def build_columns(data: Iterable[Any], config: PnFConfig) -> list[Column]:
    columns: list[Column] = []
    initial_reference: Decimal | None = None
    initial_index: int | None = None
    initial_box_size: Decimal | None = None

    for update in _iter_price_updates(data, config):
        if not columns:
            prices = _initial_prices(update, config)
            for price in prices:
                if initial_reference is None:
                    initial_reference = price
                    initial_index = update.index
                    if config.scaling == "step_box":
                        initial_box_size = calculate_step_box_size(initial_reference, config)
                    continue
                assert initial_index is not None
                column = _try_initial_column(
                    price=price,
                    index=update.index,
                    initial_index=initial_index,
                    reference=initial_reference,
                    box_size=initial_box_size,
                    config=config,
                )
                if column is not None:
                    columns.append(column)
                    break
            continue

        active = columns[-1]
        if active.type == "X":
            updated = _process_x_update(active, update, config)
        else:
            updated = _process_o_update(active, update, config)
        if updated is active:
            continue
        if updated.type == active.type:
            columns[-1] = updated
        else:
            columns.append(updated)

    return columns


def calculate_step_box_size(reference_price: Any, config: PnFConfig) -> Decimal:
    if not isinstance(config, PnFConfig):
        raise TypeError("config must be a PnFConfig instance")
    if config.scaling != "step_box":
        raise ValueError('scaling must be "step_box"')
    reference = require_positive_price(reference_price)
    if reference is None:
        raise ValueError("reference_price must be a finite positive decimal value")
    rounded_reference = _round_price(reference, config)
    box_size = decimal_mul(rounded_reference, config.box_pct_decimal)
    if box_size <= 0:
        raise ValueError("box size must be positive")
    return box_size


def calculate_logscale_box_size(reference_price: Any, config: PnFConfig) -> Decimal:
    if not isinstance(config, PnFConfig):
        raise TypeError("config must be a PnFConfig instance")
    if config.scaling != "log":
        raise ValueError('scaling must be "log"')
    reference = require_positive_price(reference_price)
    if reference is None:
        raise ValueError("reference_price must be a finite positive decimal value")
    rounded_reference = _round_price(reference, config)
    box_size = decimal_mul(rounded_reference, config.box_pct_decimal)
    if box_size <= 0:
        raise ValueError("box size must be positive")
    return box_size


def _iter_price_updates(data: Iterable[Any], config: PnFConfig) -> Iterator[PriceUpdate]:
    for index, item in enumerate(data):
        if config.method == "close":
            close = _extract_close(item)
            if close is not None:
                yield PriceUpdate(index=index, close=_round_price(close, config))
        elif config.method == "high_low":
            high, low = _extract_high_low(item)
            if high is None and low is None:
                continue
            high = _round_price(high, config) if high is not None else None
            low = _round_price(low, config) if low is not None else None
            if high is not None and low is not None and high < low:
                raise ValueError("high must be greater than or equal to low")
            yield PriceUpdate(index=index, high=high, low=low)
        else:
            high, low, close = _extract_high_low_close(item)
            if high is None and low is None and close is None:
                continue
            high = _round_price(high, config) if high is not None else None
            low = _round_price(low, config) if low is not None else None
            close = _round_price(close, config) if close is not None else None
            if high is not None and low is not None and high < low:
                raise ValueError("high must be greater than or equal to low")
            if close is not None and high is not None and close > high:
                raise ValueError("close must be less than or equal to high")
            if close is not None and low is not None and close < low:
                raise ValueError("close must be greater than or equal to low")
            yield PriceUpdate(index=index, close=close, high=high, low=low)


def _extract_close(item: Any) -> Decimal | None:
    if isinstance(item, dict):
        return require_positive_price(item.get("close"))
    return require_positive_price(item)


def _extract_high_low(item: Any) -> tuple[Decimal | None, Decimal | None]:
    if isinstance(item, dict):
        return require_positive_price(item.get("high")), require_positive_price(item.get("low"))
    if isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
        if len(item) < 2:
            raise ValueError("high_low input rows must contain high and low")
        return require_positive_price(item[0]), require_positive_price(item[1])
    raise ValueError("high_low input rows must be dicts or two-item sequences")


def _extract_high_low_close(item: Any) -> tuple[Decimal | None, Decimal | None, Decimal | None]:
    if isinstance(item, dict):
        return (
            require_positive_price(item.get("high")),
            require_positive_price(item.get("low")),
            require_positive_price(item.get("close")),
        )
    if isinstance(item, Sequence) and not isinstance(item, (str, bytes)):
        if len(item) < 3:
            raise ValueError("high_low_close input rows must contain high, low, and close")
        return (
            require_positive_price(item[0]),
            require_positive_price(item[1]),
            require_positive_price(item[2]),
        )
    raise ValueError("high_low_close input rows must be dicts or three-item sequences")


def _initial_prices(update: PriceUpdate, config: PnFConfig) -> tuple[Decimal, ...]:
    if config.method == "close":
        return () if update.close is None else (update.close,)
    values: list[Decimal] = []
    if update.high is not None:
        values.append(update.high)
    if update.low is not None:
        values.append(update.low)
    if config.method == "high_low_close" and update.close is not None:
        values.append(update.close)
    return tuple(values)


def _process_x_update(active: Column, update: PriceUpdate, config: PnFConfig) -> Column:
    reference = active.high
    if config.scaling == "log":
        return _process_log_x_update(active, update, config)
    box_size = calculate_step_box_size(reference, config)
    extension_price = update.close if config.method == "close" else update.high
    if extension_price is not None:
        boxes = _boxes_above(extension_price, reference, box_size)
        if boxes >= 1:
            return _extend_column(active, boxes, box_size, update.index, config)
    reversal_price = update.close if config.method == "close" else update.low
    if reversal_price is not None:
        boxes = _boxes_below(reversal_price, reference, box_size)
        if boxes >= config.reversal:
            return _reverse_to_o(reference, boxes, box_size, update.index, config)
    close_price = update.close if config.method == "high_low_close" else None
    if close_price is not None:
        boxes = _boxes_above(close_price, reference, box_size)
        if boxes >= 1:
            return _extend_column(active, boxes, box_size, update.index, config)
        boxes = _boxes_below(close_price, reference, box_size)
        if boxes >= config.reversal:
            return _reverse_to_o(reference, boxes, box_size, update.index, config)
    return active


def _process_o_update(active: Column, update: PriceUpdate, config: PnFConfig) -> Column:
    reference = active.low
    if config.scaling == "log":
        return _process_log_o_update(active, update, config)
    box_size = calculate_step_box_size(reference, config)
    extension_price = update.close if config.method == "close" else update.low
    if extension_price is not None:
        boxes = _boxes_below(extension_price, reference, box_size)
        if boxes >= 1:
            return _extend_column(active, boxes, box_size, update.index, config)
    reversal_price = update.close if config.method == "close" else update.high
    if reversal_price is not None:
        boxes = _boxes_above(reversal_price, reference, box_size)
        if boxes >= config.reversal:
            return _reverse_to_x(reference, boxes, box_size, update.index, config)
    close_price = update.close if config.method == "high_low_close" else None
    if close_price is not None:
        boxes = _boxes_below(close_price, reference, box_size)
        if boxes >= 1:
            return _extend_column(active, boxes, box_size, update.index, config)
        boxes = _boxes_above(close_price, reference, box_size)
        if boxes >= config.reversal:
            return _reverse_to_x(reference, boxes, box_size, update.index, config)
    return active


def _process_log_x_update(active: Column, update: PriceUpdate, config: PnFConfig) -> Column:
    reference = active.high
    extension_price = update.close if config.method == "close" else update.high
    if extension_price is not None:
        boxes = _log_boxes_above(extension_price, reference, config)
        if boxes:
            return _extend_column_with_boxes(active, boxes, update.index)
    reversal_price = update.close if config.method == "close" else update.low
    if reversal_price is not None:
        boxes = _log_boxes_below(reversal_price, reference, config)
        if len(boxes) >= config.reversal:
            return _new_column("O", boxes, update.index)
    close_price = update.close if config.method == "high_low_close" else None
    if close_price is not None:
        boxes = _log_boxes_above(close_price, reference, config)
        if boxes:
            return _extend_column_with_boxes(active, boxes, update.index)
        boxes = _log_boxes_below(close_price, reference, config)
        if len(boxes) >= config.reversal:
            return _new_column("O", boxes, update.index)
    return active


def _process_log_o_update(active: Column, update: PriceUpdate, config: PnFConfig) -> Column:
    reference = active.low
    extension_price = update.close if config.method == "close" else update.low
    if extension_price is not None:
        boxes = _log_boxes_below(extension_price, reference, config)
        if boxes:
            return _extend_column_with_boxes(active, boxes, update.index)
    reversal_price = update.close if config.method == "close" else update.high
    if reversal_price is not None:
        boxes = _log_boxes_above(reversal_price, reference, config)
        if len(boxes) >= config.reversal:
            return _new_column("X", boxes, update.index)
    close_price = update.close if config.method == "high_low_close" else None
    if close_price is not None:
        boxes = _log_boxes_below(close_price, reference, config)
        if boxes:
            return _extend_column_with_boxes(active, boxes, update.index)
        boxes = _log_boxes_above(close_price, reference, config)
        if len(boxes) >= config.reversal:
            return _new_column("X", boxes, update.index)
    return active


def _try_initial_column(
    price: Decimal,
    index: int,
    initial_index: int,
    reference: Decimal,
    box_size: Decimal | None,
    config: PnFConfig,
) -> Column | None:
    if config.scaling == "log":
        up_boxes = _log_boxes_above(price, reference, config)
        if len(up_boxes) >= config.reversal:
            return _new_column("X", up_boxes, index, start_index=initial_index)
        down_boxes = _log_boxes_below(price, reference, config)
        if len(down_boxes) >= config.reversal:
            return _new_column("O", down_boxes, index, start_index=initial_index)
        return None
    assert box_size is not None
    up_boxes = _boxes_above(price, reference, box_size)
    if up_boxes >= config.reversal:
        boxes = tuple(
            _round_price(decimal_add(reference, decimal_mul_int(box_size, step)), config)
            for step in range(1, up_boxes + 1)
        )
        return Column(
            type="X",
            box_count=len(boxes),
            high=max(boxes),
            low=min(boxes),
            start_index=initial_index,
            end_index=index,
            boxes=boxes,
        )
    down_boxes = _boxes_below(price, reference, box_size)
    if down_boxes >= config.reversal:
        boxes = tuple(
            _round_price(decimal_sub(reference, decimal_mul_int(box_size, step)), config)
            for step in range(1, down_boxes + 1)
        )
        return Column(
            type="O",
            box_count=len(boxes),
            high=max(boxes),
            low=min(boxes),
            start_index=initial_index,
            end_index=index,
            boxes=boxes,
        )
    return None


def _extend_column(active: Column, boxes: int, box_size: Decimal, index: int, config: PnFConfig) -> Column:
    if active.type == "X":
        new_boxes = tuple(
            _round_price(decimal_add(active.high, decimal_mul_int(box_size, step)), config)
            for step in range(1, boxes + 1)
        )
    else:
        new_boxes = tuple(
            _round_price(decimal_sub(active.low, decimal_mul_int(box_size, step)), config)
            for step in range(1, boxes + 1)
        )
    all_boxes = active.boxes + new_boxes
    return Column(
        type=active.type,
        box_count=len(all_boxes),
        high=max(all_boxes),
        low=min(all_boxes),
        start_index=active.start_index,
        end_index=index,
        boxes=all_boxes,
    )


def _extend_column_with_boxes(active: Column, new_boxes: tuple[Decimal, ...], index: int) -> Column:
    all_boxes = active.boxes + new_boxes
    return Column(
        type=active.type,
        box_count=len(all_boxes),
        high=max(all_boxes),
        low=min(all_boxes),
        start_index=active.start_index,
        end_index=index,
        boxes=all_boxes,
    )


def _new_column(kind: str, boxes: tuple[Decimal, ...], index: int, start_index: int | None = None) -> Column:
    return Column(
        type=kind,
        box_count=len(boxes),
        high=max(boxes),
        low=min(boxes),
        start_index=index if start_index is None else start_index,
        end_index=index,
        boxes=boxes,
    )


def _reverse_to_o(reference: Decimal, boxes: int, box_size: Decimal, index: int, config: PnFConfig) -> Column:
    new_boxes = tuple(
        _round_price(decimal_sub(reference, decimal_mul_int(box_size, step)), config)
        for step in range(1, boxes + 1)
    )
    return _new_column("O", new_boxes, index)


def _reverse_to_x(reference: Decimal, boxes: int, box_size: Decimal, index: int, config: PnFConfig) -> Column:
    new_boxes = tuple(
        _round_price(decimal_add(reference, decimal_mul_int(box_size, step)), config)
        for step in range(1, boxes + 1)
    )
    return _new_column("X", new_boxes, index)


def _round_price(price: Decimal, config: PnFConfig) -> Decimal:
    return decimal_round_nearest(price, config.tick_size_decimal)


def _next_log_box(reference: Decimal, direction: str, config: PnFConfig) -> Decimal:
    box_size = calculate_logscale_box_size(reference, config)
    if direction == "up":
        next_box = _round_price(decimal_add(reference, box_size), config)
        if next_box <= reference:
            raise ValueError("box_pct is too small for tick_size to advance an upward log box")
        return next_box
    next_box = _round_price(decimal_sub(reference, box_size), config)
    if next_box <= 0:
        raise ValueError("downward log box produced a non-positive price")
    if next_box >= reference:
        raise ValueError("box_pct is too small for tick_size to advance a downward log box")
    return next_box


def _log_boxes_above(price: Decimal, reference: Decimal, config: PnFConfig) -> tuple[Decimal, ...]:
    boxes: list[Decimal] = []
    current = reference
    while True:
        next_box = _next_log_box(current, "up", config)
        if price < next_box:
            break
        boxes.append(next_box)
        current = next_box
    return tuple(boxes)


def _log_boxes_below(price: Decimal, reference: Decimal, config: PnFConfig) -> tuple[Decimal, ...]:
    boxes: list[Decimal] = []
    current = reference
    while True:
        next_box = _next_log_box(current, "down", config)
        if price > next_box:
            break
        boxes.append(next_box)
        current = next_box
    return tuple(boxes)


def _boxes_above(price: Decimal, reference: Decimal, box_size: Decimal) -> int:
    move = decimal_sub(price, reference)
    if move < box_size:
        return 0
    return decimal_div_floor(move, box_size)


def _boxes_below(price: Decimal, reference: Decimal, box_size: Decimal) -> int:
    move = decimal_sub(reference, price)
    if move < box_size:
        return 0
    return decimal_div_floor(move, box_size)
