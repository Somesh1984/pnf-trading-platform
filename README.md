# PnF Trading Platform

Production-oriented trading platform around a deterministic Point and Figure
(PnF) core library.

## Current Milestone

`M1 Foundation` from `PLAN.MD`.

The foundation milestone creates the project base, local QuestDB service,
runtime configuration, logging, a health-check CLI, and starter documentation.

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

## chart_pnf

`chart_pnf` is the main Point and Figure chart library for this project.

Basic close-price example:

```python
from chart_pnf import PointFigureChart

chart = PointFigureChart(
    ts={"close": [100, 103, 107.12]},
    method="cl",
    reversal=3,
    boxsize=1,
    scaling="log",
)

print(chart.matrix)
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

## Tests

Run:

```powershell
python -m compileall pnf tests trading_app
python -m pytest -q
```

## Roadmap

Follow `PLAN.MD` milestone order. GitHub Project issues should map to the
milestones in `PLAN.MD`.
