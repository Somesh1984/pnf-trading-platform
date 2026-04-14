# PnF Trading Platform

Production-oriented trading platform around a deterministic Point and Figure
(PnF) core library.

## Current Milestone

`M2 PnF Core Stable` from `PLAN.MD`.

This milestone focuses on deterministic Point and Figure behavior: chart
building, step-frozen log scaling, methods, patterns, signals, trendlines,
levels, counts, rendering, docs, and comparison checks.

## Safety

This project is paper-first. Live trading is disabled by default:

```text
TRADING_MODE=paper
LIVE_TRADING_ENABLED=false
```

Live execution must not be added until historical replay, paper trading, risk
checks, and manual Telegram confirmation are complete.

## Setup

Create a virtual environment and install test dependencies as needed:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install pytest
```

Create local runtime settings:

```powershell
Copy-Item .env.example .env
```

Do not commit `.env`.
The app reads `.env` automatically; shell environment variables override file values.

## QuestDB

Start QuestDB:

```powershell
docker compose up -d questdb
```

QuestDB endpoints:

- Web console: `http://localhost:19000`
- ILP: `localhost:19009`
- Postgres wire: `localhost:18812`

QuestDB still listens on `9000`, `9009`, and `8812` inside the container. The
host ports default to `19000`, `19009`, and `18812` to avoid common local port
conflicts. Change `QUESTDB_HTTP_PORT`, `QUESTDB_ILP_PORT`, or
`QUESTDB_PG_PORT` in `.env` if you need other host ports.

## CLI

Show redacted config:

```powershell
python -m trading_app.cli show-config
```

Check QuestDB health:

```powershell
python -m trading_app.cli health
```

## PnF Usage

Use `chart_pnf.PointFigureChart` for chart work in this project.

`chart_pnf` builds the Point and Figure chart. It does not connect to Fyers,
write to QuestDB, send Telegram messages, or place orders.

Basic close-price example:

```python
from chart_pnf import PointFigureChart

chart = PointFigureChart(
    ts={"close": [100, 101, 102, 103, 100, 99, 98]},
    method="cl",
    reversal=3,
    boxsize=1,
    scaling="log",
)

print(chart.matrix)
print(chart.boxscale)
print(chart.pnf_timeseries["trend"])
```

High/low example:

```python
from chart_pnf import PointFigureChart

chart = PointFigureChart(
    ts={
        "high": [100, 102, 104, 103],
        "low": [100, 101, 99, 98],
    },
    method="h/l",
    reversal=3,
    boxsize=1,
    scaling="log",
)

print(chart.matrix)
```

Output inspection:

```python
print(chart.boxscale)       # price levels used by matrix rows
print(chart.matrix)         # X/O grid: 1 = X, -1 = O, 0 = empty
print(chart.pnf_timeseries) # per input point chart state
print(str(chart))           # readable text chart
```

### Methods

`method="cl"` uses close only:

```text
close
```

Use this when you want the simplest close-based chart.

`method="h/l"` uses high first, then low:

```text
high -> low
```

Use this when the candle high should get priority.

`method="l/h"` uses low first, then high:

```text
low -> high
```

Use this when the candle low should get priority.

`method="hlc"` uses close confirmation:

```text
close confirms
high/low fills boxes
```

Use this when you want candle data but do not want high/low touches to change
the chart unless close confirms the move.

`method="ohlc"` uses candle order:

```text
bullish candle: open -> low -> high -> close
bearish candle: open -> high -> low -> close
```

Use this for OHLC candle-path approximation. OHLC data does not contain the
real tick order inside the candle, so `cl` or `hlc` is usually clearer for
trading and replay checks.

### Scaling

`scaling="log"` uses step-frozen percentage boxes:

```text
box_size = current column last box price * box percentage
```

The box size is frozen for the full candle/update. This is the recommended
scaling for project logic.

`scaling="log_compounding"` uses a compatibility logarithmic grid:

```text
one global compounding price grid
```

Use this when you need compatibility behavior for comparison.

Other supported scaling modes are:

- `abs`: fixed absolute box size
- `cla`: classic box size table
- `atr`: ATR-based box size

Recommended combinations:

```python
PointFigureChart(ts=data, method="cl", scaling="log")
PointFigureChart(ts=data, method="hlc", scaling="log")
PointFigureChart(ts=data, method="h/l", scaling="log")
PointFigureChart(ts=data, method="l/h", scaling="log")
PointFigureChart(ts=data, method="ohlc", scaling="log")
```

### Config Values

- `ts`: input data dictionary.
- `method`: price path to use from each input row.
- `reversal`: boxes needed to reverse into a new column.
- `boxsize`: box percentage when `scaling="log"`.
- `scaling`: use `"log"` for step-frozen percentage boxes.

For `scaling="log"` and `boxsize=1`, each box is 1% of the active reference
box price for that candle/update.

### Core Boundary

`pnf/` and `chart_pnf/` must stay deterministic.

Do not put these inside PnF code:

- Fyers API calls
- QuestDB writes
- Telegram messages
- paper/live order execution
- environment variable reads

Those belong in `trading_app/` and later milestones.

## Tests

Run:

```powershell
python -m compileall chart_pnf pnf tests trading_app
python -m pytest -q
```

## Roadmap

Follow `PLAN.MD` milestone order. GitHub Project issues should map to the
milestones in `PLAN.MD`.
