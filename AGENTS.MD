# AGENTS.MD

## 1. Role

You are a senior quant developer specialized in Point & Figure (PnF) charts.

You are also responsible for building the surrounding trading platform described
in `PLAN.MD`.

Your responsibilities:

* build production-grade PnF library
* build the Fyers + QuestDB + Telegram + execution platform around it
* write clean, modular, testable Python code
* follow strict deterministic financial logic (no assumptions)
* follow `PLAN.MD` milestone order before implementing project work

If any rule is unclear -> ASK before implementing.

---

## 2. Project Goal

Build a reusable, deterministic PnF library with:

* column generation engine
* pattern detection
* trendlines
* support/resistance
* horizontal count
* vertical count
* trading strategy layer

The full platform goal is defined in `PLAN.MD`.

The PnF library is the deterministic core. The trading platform is built around
that core. Platform work must never weaken or bypass the PnF rules in this file.

`PLAN.MD` is the local source of truth for roadmap and milestone sequence.
GitHub Project is the task tracker and progress board.

---

## 3. Configuration (MANDATORY)

All logic must depend on a config object:

```python
class PnFConfig:
    box_pct: float          # e.g. 0.0025 for 0.25%
    reversal: int           # e.g. 3
    method: str             # "close" or "high_low"
    scaling: str            # "log" = step-frozen percentage scaling
```

Rules:

* box_pct > 0
* reversal >= 1
* scaling must be "log"
* `"log"` is the public config value, but implementation must follow the step-frozen percentage box rule
* `"log"` must NOT be implemented as a global logarithmic box-index grid
* invalid config -> raise error

---

## 4. Input Data Rules

* input = ordered time series

* format:

  * if method == "close" -> use close only
  * if method == "high_low" -> use high/low

* missing data:

  * do NOT fill -> process as-is

* gaps:

  * allow multi-box jumps in single step

---

## 5. Box Calculation (STRICT)

Scaling mode:

* `scaling` must be `"log"`
* in this project, `"log"` means step-frozen percentage-derived box sizing
* do NOT use a global log-index formula for all prices

Step-frozen percentage box rule:

```text
reference_price = current column last box price
box_size = reference_price * box_pct
continuation_value = reference_price +/- box_size
reversal_value = reference_price +/- (reversal * box_size)
```

Rules:

* box size is calculated from the last completed/current box price
* once a new candle/update starts, that box size is frozen for the entire candle/update
* if the same candle/update creates 10 boxes, all 10 boxes use the same frozen box size
* do NOT compound box size inside the same candle/update
* after the candle/update is fully processed, calculate the next box size from the new last box
* continuation and reversal thresholds for the next candle/update must be fixed from that new last box
* no linear approximation beyond this explicitly defined frozen-step rule is allowed
* no rounding shortcuts

Implementation requirement:

* use fixed precision math or controlled Decimal calculations
* use integer box counts for how many boxes a candle/update creates
* floating drift must be controlled

---

## 6. Initialization (CRITICAL)

At start:

* no column exists

First column forms ONLY IF:

```text
price moves >= reversal * box_size
```

Rules:

* initial reference price = first valid price
* initial box size = initial reference price * box_pct
* initial box size is frozen until the first column forms
* until threshold reached -> no column
* first column direction = direction of breakout move

---

## 7. Column Structure

Each column:

```python
class Column:
    type: str          # 'X' or 'O'
    box_count: int
    high: float
    low: float
    start_index: int
    end_index: int
```

Rules:

* column is immutable after reversal
* no repainting allowed

---

## 8. Column Generation Logic

Definitions:

* X column = rising
* O column = falling

Rules:

### Extension

* X column:

  * at candle/update start, calculate `box_size = last_high * box_pct`
  * freeze this box size for the entire candle/update
  * extend if price >= last_high + box_size
  * if multiple X boxes are created, each box uses the same frozen box size

* O column:

  * at candle/update start, calculate `box_size = last_low * box_pct`
  * freeze this box size for the entire candle/update
  * extend if price <= last_low - box_size
  * if multiple O boxes are created, each box uses the same frozen box size

### Reversal

```text
reversal_threshold = reversal * box_size
```

* from X -> O:

  * calculate reversal threshold from the X column last high at candle/update start
  * if price <= last_high - reversal_threshold
  * reversal O boxes use the same frozen box size for that candle/update

* from O -> X:

  * calculate reversal threshold from the O column last low at candle/update start
  * if price >= last_low + reversal_threshold
  * reversal X boxes use the same frozen box size for that candle/update

Rules:

* no intra-column direction change
* one price update can create multiple boxes
* after all boxes for the candle/update are created, update the active column last box
* next candle/update recalculates box size from that latest last box

---

## 9. Pattern Detection (STRICT)

Supported patterns ONLY:

* double top breakout
* double bottom breakdown
* triple top/bottom
* bullish catapult
* bearish catapult

Rules:

* column-based logic ONLY
* breakout condition = STRICT `>` (not >=)
* equal highs/lows must be handled explicitly
* define minimum columns required per pattern
* avoid false breakouts:

  * must confirm with prior columns

---

## 10. Trendlines

Rules:

* bullish support line:

  * 45 degree from lowest O column

* bearish resistance:

  * 45 degree from highest X column

Implementation:

* grid-based (box coordinates, NOT price directly)

Break condition:

* line break only if full box violation

---

## 11. Support / Resistance

Rules:

* detect horizontal congestion

* minimum touches >= 3

* cluster nearby levels:

  * threshold must be defined in box units

* ignore weak/noisy levels

---

## 12. Horizontal Count

Steps:

1. identify congestion zone
2. count columns in range

Formula:

```text
target = columns x box_size x reversal
```

Rules:

* define start/end columns explicitly
* exclude outliers

---

## 13. Vertical Count

Steps:

1. identify breakout column
2. count boxes in that column

Formula:

```text
target = boxes x box_size x reversal
```

Rules:

* use FIRST valid breakout column only
* ignore continuation columns

---

## 14. Trading Logic (READ-ONLY LAYER)

Combine:

* patterns
* trendlines
* support/resistance
* counts

Rules:

* DO NOT modify PnF structure

* require confirmation (no raw breakout)

* must include:

  * entry
  * stop loss
  * target

* avoid overtrading

---

## 15. Architecture

```text
pnf/
    core.py
    patterns.py
    trendlines.py
    levels.py
    counts.py
    strategy.py
    render.py
    utils.py
```

Canonical module paths:

* `pnf/core.py`
* `pnf/patterns.py`
* `pnf/trendlines.py`
* `pnf/levels.py`
* `pnf/counts.py`
* `pnf/strategy.py`
* `pnf/render.py`
* `pnf/utils.py`

Rules:

* no circular dependencies
* each module = single responsibility

Core boundary rules:

* `pnf/` is pure deterministic PnF logic
* no Fyers imports inside `pnf/`
* no QuestDB code inside `pnf/`
* no Telegram code inside `pnf/`
* no order execution or paper execution inside `pnf/`
* no environment variable reads inside `pnf/`
* no service orchestration inside `pnf/`

Trading platform code must live outside `pnf/`, preferably under:

```text
trading_app/
    brokers/
    data/
    universe/
    strategies/
    execution/
    notifications/
    services/
```

`chart_pnf/` may be used for inspection, demo, or reference work. Production
deterministic logic should live in `pnf/`.

---

## 16. Notebook / Inspection Rendering

Purpose:

* help inspect PnF output step by step in notebooks
* display generated X/O columns clearly
* debug deterministic column generation, patterns, levels, and counts

Allowed helpers:

* `columns_to_table(columns)`
* `render_ascii_chart(columns)`
* `columns_to_rows(columns)`

Rules:

* rendering is READ-ONLY
* rendering must NOT modify columns, patterns, trendlines, levels, counts, or trades
* rendering must use completed PnF structures only
* rendering must not contain trading logic
* rendering must be deterministic
* output may be plain text or pure Python table data
* no plotting dependency is allowed in core rendering

---

## 17. Coding Rules

Core PnF rules:

* `pnf/` must remain pure Python
* `pnf/` must remain deterministic
* `pnf/` must avoid external service dependencies
* outputs must be reusable and testable

Platform rules:

* external integrations are allowed only outside `pnf/`
* broker code must be isolated behind adapter interfaces
* storage code must be isolated behind repository/writer interfaces
* Telegram code must be isolated under notifications
* execution code must always go through risk checks
* secrets must never be hardcoded
* use modular functions and single-responsibility modules

DO NOT:

* use randomness
* hardcode trading values that belong in config
* mix unrelated responsibilities

---

## 18. Performance Constraints

* must handle 100k+ data points
* avoid nested loops
* prefer:

  * incremental updates
  * integer box indexing

---

## 19. Output Rules

For code implementation:

* explain the small goal before editing
* keep explanations short and practical
* summarize changed files and tests
* use consistent naming conventions

For planning/documentation/review tasks:

* prose is allowed
* align all plans with `PLAN.MD`
* do not invent new milestones unless `PLAN.MD` is updated first

For trading/live execution:

* never suggest shortcuts that bypass paper mode, risk checks, or manual confirmation

---

## 20. Testing (MANDATORY)

* write unit tests for every module
* include:

  * edge cases
  * large dataset
  * reversal edge scenarios
  * gap handling

---

## 21. Workflow

For every implementation task:

1. read `PLAN.MD`
2. identify the exact milestone for the task
3. confirm the task belongs to the current milestone or explain why it is out of order
4. explain the small goal, likely files, acceptance criteria, and checks
5. implement the smallest correct change
6. add or update relevant tests
7. run relevant tests/checks
8. refactor only within the requested scope
9. update docs if behavior or operation changes
10. summarize what changed and what was verified

If a user asks for work outside the current milestone:

* explain the dependency risk
* suggest the correct milestone order
* ask before skipping ahead unless the user explicitly requested out-of-order work

---

## 22. Determinism Guarantee

* same input -> same output ALWAYS
* no floating inconsistencies allowed

---

## 23. Future Extensions

Keep design flexible for:

* multi box size
* multi timeframe
* live streaming updates
* backtesting engine

---

## 24. PLAN.MD Governance

`PLAN.MD` is the master roadmap and local source of truth for milestone order.

Rules:

* read `PLAN.MD` before starting implementation work
* identify the exact milestone before making changes
* do not skip milestones unless the user explicitly approves
* do not add major architecture outside `PLAN.MD`
* if scope changes, update `PLAN.MD` first
* every implementation task must map to exactly one milestone
* work in small, complete, testable steps

Milestone order must follow `PLAN.MD`.

---

## 25. GitHub Project Discipline

GitHub Project is the task tracker and progress board. It mirrors `PLAN.MD`; it
does not replace it.

Every GitHub issue must include:

* Goal
* Scope
* Out of scope
* Tasks
* Tests
* Done criteria

Project fields must match `PLAN.MD`:

* Status
* Milestone
* Component
* Priority
* Risk
* Effort
* Acceptance
* Dependency

If GitHub Project and `PLAN.MD` conflict, pause and ask the user which one is
correct.

---

## 26. Explain Then Execute Workflow

For every implementation task, Codex must first explain:

* current milestone
* exact small goal
* files likely to change
* acceptance criteria
* tests/checks to run

After that, Codex may execute the task in the same turn if the user has asked
for implementation.

Codex must pause and ask before:

* live broker execution
* modifying secrets or credentials
* destructive commands
* deleting data
* changing core architecture
* skipping a milestone

---

## 27. Small Step Discipline

Do not implement large milestones in one pass.

Each task should be small enough to complete with:

* focused code changes
* relevant tests
* clear verification
* short final summary

Prefer completing one GitHub issue fully before starting another. Do not mix
unrelated milestones in the same change.

---

## 28. Historical-First Rule

Historical data ingestion and replay must be completed before live signal
generation.

Rules:

* historical data must be stored before strategy validation
* replay must be deterministic
* live candle builder and replay must share the same logic
* paper trading starts only after historical replay is stable

---

## 29. Trading Platform Safety

Trading safety is mandatory.

Rules:

* paper trading must be completed before live trading
* live mode must be off by default
* live orders require Telegram manual confirmation
* every order must pass risk checks
* duplicate signals must be prevented
* duplicate orders must be prevented
* every signal/order/fill must be auditable
* kill switch must block new orders
* no live execution code may bypass the risk engine

Initial live execution must use tiny quantity only.

---

## 30. Data Pipeline Rules

Market data rules:

* store raw ticks before building candles
* build candles only from stored or normalized ticks
* strategy consumes closed candles only
* unfinished candles must not generate final trading signals
* replay and live processing must produce identical output for identical input
* malformed ticks must be rejected or quarantined, not silently fixed
* duplicate and out-of-order ticks must be handled deterministically

Required candle intervals for v1:

* 5 seconds
* 1 minute

---

## 31. Broker Integration Rules

Fyers integration rules:

* all Fyers code must live outside `pnf/`
* broker APIs must be wrapped behind interfaces
* tests must use fake broker adapters where possible
* auth tokens must never be committed
* reconnect/backoff behavior is required for live data
* order reconciliation is required before live trading is considered complete

---

## 32. Storage Rules

QuestDB rules:

* QuestDB is used for time-series data
* ticks, candles, signals, and PnF inspection data may be stored in QuestDB
* writes should be batched
* timestamps must be explicit and deterministic
* storage code must not be inside `pnf/`

Control state rules:

* approvals, orders, positions, idempotency keys, and risk state require transactional storage
* do not rely on QuestDB alone for order-control state

---

## 33. Documentation And Runbooks

Documentation is required for operational behavior.

Update docs when changing:

* setup
* configuration
* broker auth
* QuestDB schema
* service startup
* replay behavior
* Telegram commands
* risk limits
* live execution behavior
* recovery process

Before live execution, a runbook must exist.

---

## 34. Definition Of Done

A task is done only when:

* requested scope is implemented
* relevant tests/checks pass or failures are clearly reported
* no unrelated files are changed
* no secrets are committed
* deterministic behavior is preserved
* final response explains what changed and what was verified
