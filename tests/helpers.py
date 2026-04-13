from __future__ import annotations

from decimal import Decimal

from pnf.core import Column


def make_column(kind: str, low: str, high: str, index: int, count: int | None = None) -> Column:
    low_value = Decimal(low)
    high_value = Decimal(high)
    box_count = count if count is not None else 1
    boxes = (high_value,) if kind == "X" else (low_value,)
    if box_count > 1:
        if kind == "X":
            boxes = tuple(low_value + Decimal(step) for step in range(box_count))
        else:
            boxes = tuple(high_value - Decimal(step) for step in range(box_count))
    return Column(
        type=kind,
        box_count=box_count,
        high=high_value,
        low=low_value,
        start_index=index,
        end_index=index,
        boxes=boxes,
    )
