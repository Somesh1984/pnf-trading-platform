# PnF Trading Platform Plan (Lean)

## 1. Goal
Deterministic PnF-based trading platform with:
- Fyers integration
- Historical + live data pipelines
- QuestDB storage
- Candle generation (5s, 1m)
- PnF signals
- Telegram alerts + approvals
- Paper trading → manual live execution
- Risk control + replay

---

## 2. Non-Negotiable Rules
- PnF core deterministic, broker-independent
- Store raw ticks before candles
- Strategy uses CLOSED candles only
- Historical → Replay → Paper → Live (strict)
- Live & replay share same logic
- Same input → same output
- No duplicate signals/orders
- Risk check mandatory
- Live requires manual approval

---

## 3. Architecture

Historical:
Fyers API → Normalize → QuestDB → Replay → Strategy → Signals → Report

Live:
Fyers Socket → Normalize → QuestDB → Candle → Strategy → Signals → Telegram → Approval → Execution → Reconciliation

---

## 4. Milestones

### M1 Foundation
- Repo setup, env, config, logging, QuestDB, CLI, health check, README  
Done: app runs, config loads, QuestDB works, no secrets

### M2 PnF Core Stable
- Validate config, box logic, reversal/gap, replay determinism  
Done: deterministic output, all tests pass, no external deps

### M3 Fyers Auth + Symbols
- Auth flow, token, symbol cache, broker interface, fake broker  
Done: env creds load, symbols work, no real dependency needed

### M4 Universe Builder
- Equity/index list, ATM calc, option strikes, CE/PE, store universe  
Done: deterministic universe, shard-compatible, reproducible

### M5 Historical Data Ingestion
- Fetch candles, store in QuestDB, metadata, retry, dedup, batching  
Done: queryable data, no duplicates, retry works, testable

### M6 Candle Builder From Historical Data
- Load, normalize, validate OHLC, store canonical candles  
Done: deterministic candles, invalid rejected, replay-ready

### M7 Historical Replay + PnF Signals
- Replay engine, feed candles, generate signals, dedup, report  
Done: deterministic signals, no duplicates, basic report

### M8 Live Tick Storage
- DataSocket, normalize ticks, QuestDB write, reconnect, metrics  
Done: ticks stored, schema consistent, reconnect works

### M9 Live Candle Builder
- Build 5s/1m candles, handle missing/duplicate/out-of-order ticks  
Done: same logic as replay, closed candles only, deterministic

### M10 Telegram Alerts
- Bot, alerts, approve/reject, kill-switch, state store  
Done: 1 signal = 1 message, approval persisted

### M11 Paper Trading
- Orders, fills, SL/target, positions, PnL, tests  
Done: deterministic PnL, no duplicate orders

### M12 Risk Engine
- Trade limits, loss limits, qty/value, market hours, kill-switch  
Done: all orders pass risk, rejection reason logged

### M13 Manual Live Execution
- Fyers orders, approval gate, reconciliation, idempotency  
Done: manual approval required, no duplicate execution

### M14 Ops + Recovery
- Scheduler, restart, replay, monitoring, runbook  
Done: safe restart, replayable, recovery defined

---

## 5. GitHub Project Setup

Fields:
- Status: Backlog → Done
- Milestone: M1 → M14
- Component, Priority, Risk, Effort, Acceptance, Dependency

Views:
- Roadmap, Sprint, Component, P0, Blocked, Current

---

## 6. First Sprint
Ready only:
- Git init
- .gitignore
- .env.example
- QuestDB docker
- config loader
- logging
- health check
- README

Rest = Backlog

---

## 7. Acceptance Policy
Every issue must include:
- Goal, Scope, Tasks, Tests, Done criteria

Done only if:
- Tests pass
- Deterministic behavior
- No secrets
- Good logs
- PnF rules intact