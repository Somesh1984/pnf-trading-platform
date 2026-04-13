# PnF Trading Platform Plan

## 1. Goal
Build a full trading platform around the deterministic PnF library:
- Fyers broker integration
- Historical data ingestion
- Live tick data ingestion
- QuestDB tick/candle storage
- 5-second and 1-minute candle generation
- PnF strategy signals
- Telegram alerts
- Paper trading
- Manual-confirm live execution
- Risk controls
- Replay and recovery

## 2. Non-Negotiable Rules
- PnF core remains deterministic and broker-independent.
- Store raw ticks before building candles.
- Strategy consumes only closed candles.
- Historical data pipeline must be completed before live signal generation.
- Historical replay must produce deterministic signals before paper trading.
- Live candle builder and historical replay must share the same candle/strategy logic.
- Historical data must be stored/queryable before strategy validation.
- Paper trading comes before live trading.
- Live trading requires Telegram manual confirmation.
- Every order must pass risk checks.
- No duplicate signals or duplicate orders.
- Same input data must produce same output.

## 3. Architecture

Historical path:

Fyers Historical API
-> Historical normalizer
-> QuestDB historical candles/ticks
-> Replay engine
-> Candle/PnF strategy runner
-> Historical signals
-> Backtest/report output

Live path:

Fyers DataSocket
-> Tick normalizer
-> QuestDB ticks
-> Candle builder
-> QuestDB candles
-> PnF strategy runner
-> Signals
-> Telegram notifier
-> Manual approval
-> Paper/live executor
-> Reconciliation

## 4. Milestones
### M1 Foundation
Goal: clean project base.

Tasks:
- Initialize Git repo
- Add `.gitignore`
- Add `.env.example`
- Add Docker Compose for QuestDB
- Add config loader
- Add logging setup
- Add CLI entrypoint
- Add health check
- Add README skeleton

Done when:
- App starts locally
- QuestDB runs in Docker
- Config loads from env
- No secrets are committed

### M2 PnF Core Stable
Goal: deterministic PnF library ready.

Tasks:
- Validate `PnFConfig`
- Confirm step-frozen percentage box logic
- Add reversal/gap tests
- Add large dataset test
- Add deterministic replay test
- Keep `pnf/` independent

Done when:
- All PnF tests pass
- Same input gives same columns
- No broker/storage/execution code inside `pnf/`

### M3 Fyers Auth + Symbols
Goal: broker connection foundation.

Tasks:
- Add Fyers config
- Add manual auth/token flow
- Add token storage
- Add symbol master cache
- Add broker adapter interface
- Add fake broker for tests

Done when:
- Credentials load from env
- Symbol lookup works
- Tests run without real Fyers connection

### M4 Historical Data Ingestion
Goal: Fyers se historical data lena aur QuestDB me store karna.

Tasks:
- Add Fyers historical data adapter
- Define historical data request config
- Fetch historical candles for equities, indexes, and options where available
- Store historical candles in QuestDB
- Add symbol/date/timeframe metadata
- Add duplicate candle handling
- Add retry/backoff for failed requests
- Add rate-limit friendly batch downloader
- Add download progress logs
- Add historical ingestion tests with fake Fyers responses

Done when:
- Historical OHLCV data QuestDB me stored ho
- Same request duplicate records create na kare
- Failed downloads retry/report hon
- Downloaded data can be queried by symbol, date, timeframe
- Tests real Fyers connection ke bina pass hon

### M5 Universe Builder
Goal: daily tradable universe decide karna.

Tasks:
- Load 200 equity symbols
- Add 2 index symbols
- Use historical daily/open data to calculate ATM strike
- Generate ATM +/- 10 strikes
- Generate CE/PE option symbols
- Store daily universe
- Split symbols into Fyers subscription shards

Done when:
- Same date/open input creates same universe
- Universe can be recreated historically
- Symbol count is within Fyers shard limits
- Universe is logged and stored

### M6 Candle Builder From Historical Data
Goal: historical data se deterministic candles create/validate karna.

Tasks:
- Load historical candles from QuestDB
- If historical tick data is available, build 5s/1m candles from ticks
- If only broker historical candles are available, mark source as broker historical candle
- Normalize candle schema
- Validate OHLC consistency
- Store canonical candles in QuestDB
- Add replay fixtures

Done when:
- Historical candles are queryable in canonical schema
- Same historical source produces same candle output
- Invalid candles are rejected or quarantined
- 5s/1m candle behavior is testable before live mode

### M7 Historical Replay + PnF Signals
Goal: live trading se pehle historical replay par strategy validate karna.

Tasks:
- Add replay engine
- Replay candles symbol-by-symbol and timeframe-by-timeframe
- Feed closed candles into PnF engine
- Generate historical signals
- Persist signals
- Add signal deduplication
- Add basic backtest report
- Compare repeated replay output for determinism

Done when:
- Same historical data se same signals every run
- Signals include entry, stop, target
- Duplicate signals are not generated
- Basic report shows trades/signals by symbol/date/timeframe

### M8 Live Tick Storage
Goal: Fyers ticks stored in QuestDB.

Tasks:
- Add Fyers DataSocket connector
- Normalize live ticks
- Add QuestDB ILP writer
- Batch tick writes
- Add reconnect/backoff
- Add ingestion health metrics

Done when:
- Live ticks are visible in QuestDB
- Historical and live data schema are compatible
- Malformed ticks are handled
- Reconnect works after disconnect

### M9 Live Candle Builder
Goal: live ticks se deterministic 5s and 1m candles banana.

Tasks:
- Build 5-second OHLCV candles from live ticks
- Build 1-minute OHLCV candles from live ticks
- Store closed candles only
- Handle missing ticks
- Handle duplicate ticks
- Handle out-of-order ticks
- Compare live-built candles with replay logic

Done when:
- Live and replay candle builder use the same logic
- Same ticks produce same candles
- Candle close triggers strategy event
- Strategy receives only closed candles

### M10 Telegram Alerts
Goal: send actionable alerts.

Tasks:
- Add Telegram bot config
- Add message templates
- Send signal alert
- Add approve command
- Add reject command
- Add kill-switch command
- Persist approval state

Done when:
- One signal creates one Telegram message
- Approval/reject is stored
- Kill switch blocks new orders

### M11 Paper Trading
Goal: validate full execution flow without real money.

Tasks:
- Add paper order model
- Add paper fill simulator
- Add stop loss handling
- Add target handling
- Track positions
- Add daily PnL report
- Add paper execution tests

Done when:
- Approved signals create paper orders
- PnL is deterministic
- Duplicate paper orders are impossible

### M12 Risk Engine
Goal: mandatory risk controls.

Tasks:
- Add max trades per day
- Add max daily loss
- Add max quantity/order value
- Add one-position-per-symbol rule
- Add market-hours check
- Add kill-switch guard
- Add risk rejection tests

Done when:
- Every order passes through risk engine
- Rejected orders include reason
- Execution cannot bypass risk

### M13 Manual Live Execution
Goal: tiny real order after manual approval.

Tasks:
- Add Fyers order adapter
- Place live order only after Telegram approval
- Add order status reconciliation
- Add tradebook reconciliation
- Add position reconciliation
- Add idempotency key
- Add emergency cancel/exit command

Done when:
- Live mode is off by default
- Manual approval is required
- Risk approval is required
- Duplicate live order cannot happen

### M14 Ops + Recovery
Goal: reliable daily operation.

Tasks:
- Add daily startup checklist
- Add market open/close scheduler
- Add restart behavior
- Add replay command
- Add backup notes
- Add runbook
- Add monitoring queries

Done when:
- Restart does not duplicate signals/orders
- Any day can be replayed
- Failure recovery is documented

## 5. GitHub Project Setup
Project name:
`PnF Trading Platform`

Fields:
- `Status`: Backlog, Ready, In Progress, Review, Blocked, Done
- `Milestone`: M1 Foundation, M2 PnF Core Stable, M3 Fyers Auth + Symbols, M4 Historical Data Ingestion, M5 Universe Builder, M6 Candle Builder From Historical Data, M7 Historical Replay + PnF Signals, M8 Live Tick Storage, M9 Live Candle Builder, M10 Telegram Alerts, M11 Paper Trading, M12 Risk Engine, M13 Manual Live Execution, M14 Ops + Recovery
- `Component`: Core, Broker, Data, QuestDB, Candles, Strategy, Telegram, Execution, Risk, Infra, Tests, Docs
- `Priority`: P0, P1, P2
- `Risk`: High, Medium, Low
- `Effort`: 1, 2, 3, 5, 8
- `Acceptance`: Pending, Tests Pending, Review Pending, Passing
- `Dependency`: text or issue number

Views:
- `Roadmap`
- `Sprint Board`
- `Component Table`
- `P0 Queue`
- `Blocked`
- `Current Milestone`

## 6. First Sprint
Only these items should go to `Ready` first:

- Initialize Git repo
- Add `.gitignore`
- Add `.env.example`
- Add Docker Compose for QuestDB
- Add config loader
- Add logging setup
- Add basic health check
- Add README skeleton

Everything else remains in `Backlog`.

## 7. Acceptance Policy
Every issue must include:
- Goal
- Scope
- Out of scope
- Tasks
- Tests
- Done criteria

No issue is `Done` unless:
- Tests pass where applicable
- No secrets are committed
- Behavior is deterministic
- Logs are sufficient for debugging
- Existing PnF rules are not violated
