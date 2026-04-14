# M2 chart_pnf And pnf Core Comparison

## Purpose

This note records the #19 comparison between `chart_pnf` and `pnf.core`.

The goal is not to change project direction. `chart_pnf.PointFigureChart` is the
main chart API for this project right now. `pnf.core` is still useful as a
small deterministic reference/helper for simple column behavior.

## What Was Compared

The comparison tests use the same simple price input in both implementations:

- close-only first X column
- close-only X extension
- close-only X to O reversal
- close-only large gap
- high/low extension priority
- high/low reversal when high does not extend first

Both implementations are compared after normalizing columns to:

- column type
- sorted filled price boxes
- low
- high
- box count

## Known Representation Difference

`chart_pnf` stores columns in a matrix. Matrix rows are ordered by price, so
O-column boxes are naturally read from low price to high price.

`pnf.core` stores each column as movement boxes. O-column boxes are usually
stored from high price to low price.

Because of that, tests compare sorted box prices instead of raw internal order.
The price content matches for the simple cases covered by #19.

## Result

For the covered close and high/low examples, `chart_pnf` and `pnf.core` produce
the same normalized column content.

Broker, storage, Telegram, strategy execution, and live trading behavior are
not part of this comparison.
