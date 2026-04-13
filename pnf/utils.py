from __future__ import annotations

from decimal import Context, Decimal, InvalidOperation, ROUND_FLOOR, ROUND_HALF_UP
from math import isfinite
from typing import Any


DECIMAL_CONTEXT = Context(prec=34)


def to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        decimal_value = value
    elif isinstance(value, float):
        if not isfinite(value):
            return None
        decimal_value = Decimal(str(value))
    else:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, ValueError):
            return None
    if not decimal_value.is_finite():
        return None
    return decimal_value


def require_positive_price(value: Any) -> Decimal | None:
    decimal_value = to_decimal(value)
    if decimal_value is None:
        return None
    if decimal_value <= 0:
        raise ValueError("prices must be positive")
    return decimal_value


def decimal_add(left: Decimal, right: Decimal) -> Decimal:
    return DECIMAL_CONTEXT.add(left, right)


def decimal_sub(left: Decimal, right: Decimal) -> Decimal:
    return DECIMAL_CONTEXT.subtract(left, right)


def decimal_mul(left: Decimal, right: Decimal) -> Decimal:
    return DECIMAL_CONTEXT.multiply(left, right)


def decimal_mul_int(value: Decimal, multiplier: int) -> Decimal:
    return DECIMAL_CONTEXT.multiply(value, Decimal(multiplier))


def decimal_div_floor(numerator: Decimal, denominator: Decimal) -> int:
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    quotient = DECIMAL_CONTEXT.divide(numerator, denominator)
    return int(quotient.to_integral_value(rounding=ROUND_FLOOR))


def decimal_round_nearest(value: Decimal, tick_size: Decimal) -> Decimal:
    if tick_size <= 0:
        raise ValueError("tick_size must be greater than zero")
    units = DECIMAL_CONTEXT.divide(value, tick_size)
    rounded_units = units.to_integral_value(rounding=ROUND_HALF_UP)
    rounded = DECIMAL_CONTEXT.multiply(rounded_units, tick_size)
    return rounded.quantize(tick_size, rounding=ROUND_HALF_UP)


def decimal_mean(values: list[Decimal]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    return DECIMAL_CONTEXT.divide(sum(values, Decimal("0")), Decimal(len(values)))


def decimal_to_string(value: Decimal) -> str:
    normalized = value.normalize()
    if normalized == normalized.to_integral():
        return format(normalized, "f")
    return format(normalized, "f")
