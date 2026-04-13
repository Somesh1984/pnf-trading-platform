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

## Tests

Run:

```powershell
python -m compileall pnf tests trading_app
python -m pytest -q
```

## Roadmap

Follow `PLAN.MD` milestone order. GitHub Project issues should map to the
milestones in `PLAN.MD`.
