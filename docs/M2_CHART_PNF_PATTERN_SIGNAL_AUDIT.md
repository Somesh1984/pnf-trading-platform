# M2 chart_pnf Pattern And Signal Audit

## Purpose

This audit records the current `chart_pnf` pattern and signal behavior before we
change or trust it for strategy work.

This issue does not change trading logic. It only documents what exists, what
looks reusable, and what needs tests before live or paper use.

## Current Pattern Logic

File: `chart_pnf/chart_patterns.py`

Current public methods:

- `get_breakouts()`
- `get_trendlines(length=4, mode="strong")`

`get_breakouts()` reads the completed chart matrix and action index matrix. It
does not read broker, storage, or platform data.

Breakout output keys:

- `ts index`
- `trend`
- `type`
- `column index`
- `box index`
- `hits`
- `width`
- `outer width`

Current breakout type values are text values such as:

- `conti`
- `resistance`
- `fulcrum`
- `reversal`

`get_trendlines()` also works from the completed chart matrix. It returns
trendline data with type, length, column index, and box index.

## Current Signal Logic

File: `chart_pnf/chart_signals.py`

Current public methods:

- `next_simple_signal()`
- `get_buy_sell_signals()`
- `get_triangles(strict=False)`
- `get_high_low_poles()`
- `get_traps()`
- `get_asc_desc_triple_breakouts()`
- `get_catapults()`
- `get_reversed_signals()`
- `get_double_breakouts()`
- `get_triple_breakouts()`
- `get_spread_triple_breakouts()`
- `get_quadruple_breakouts()`
- `get_signals()`

Signal output keys:

- `box index`
- `top box index`
- `bottom box index`
- `type`
- `width`
- `ts index`

`get_signals()` calls several signal methods in sequence and writes into one
shared `self.signals` dictionary.

Signal names live in `SIGNAL_TYPES` in `chart_pnf/chart_shared.py`. The signal
output stores numeric `type` values, not names.

## What Looks Reusable Now

- Pattern and signal code uses chart output, not broker or platform services.
- The logic is deterministic for the same completed matrix input.
- Breakout output has useful fields for later strategy validation.
- Signal output has enough fields to map a signal back to price boxes and source
  time index.
- `next_simple_signal()` can be useful for inspection, but it is not enough for
  automated trading.

## What Needs Tests Before Trust

- Breakout type behavior needs explicit examples for bullish and bearish cases.
- Numeric signal `type` values need tests against `SIGNAL_TYPES`.
- `get_signals()` ordering needs tests because later methods can overwrite or
  skip earlier signal fields.
- Double and triple breakout behavior needs small known examples.
- Catapult, trap, triangle, pole, and reversed-signal behavior needs separate
  examples before any strategy uses them.
- Trendline behavior should be tested separately before counts or strategy use.

## Naming And Comment Cleanup Needed

- `type` in signal output is numeric, but the meaning is hidden in
  `SIGNAL_TYPES`.
- `conti` should be documented or renamed later because it is not clear.
- Some comments describe drawing/plot behavior mixed with pattern behavior.
- Some method names are clear, but the output fields need a small helper or
  documentation before strategy use.

## Do Not Use For Live Trading Yet

Do not use `get_signals()` output directly for live or paper orders yet.

Before trading use, we need:

- tests for each signal type we plan to support
- stable mapping from numeric signal type to signal name
- clear entry, stop, and target rules outside the chart code
- duplicate signal prevention in the platform layer
- historical replay validation

## Recommended Next Work Order

1. `#21` Check `chart_pnf` pattern and signal logic
2. `#32` Check strategy output fields
3. `#29` Check PnF trendline logic
4. `#30` Check support and resistance level logic
5. `#31` Check horizontal and vertical count logic
6. `#24` Clean `chart_pnf` naming and comments

## Audit Result

`chart_pnf` pattern and signal code is useful as an inspection and test target,
but it is not ready for trading decisions without more behavior tests.

The next safe step is to add focused tests for breakout and signal behavior
before changing names, comments, counts, strategy, or live platform logic.
