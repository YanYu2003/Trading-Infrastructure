# US Equity Mini Trading Infrastructure

美股实时行情接入与 Mini OMS 模拟交易系统。

This project is a resume-oriented trading infrastructure project. It demonstrates how a Mini OMS can receive market data events, generate simple strategy signals, run pre-trade risk checks, manage order lifecycle, simulate broker fills, and update positions, cash, and PnL.

It is not investment advice. The default mode is mock trading. Live trading is out of scope for the MVP.

## Safety Stance

- Default execution is `mock`.
- Paper trading may be added later through explicit adapters.
- Live trading is disabled by default and is not part of the MVP.
- API keys, tokens, passwords, and broker credentials must never be committed.

## MVP Scope

The first runnable version will include:

- CLI demo plus pytest tests
- deterministic mock market data
- price threshold strategy
- Mini OMS order lifecycle
- pre-trade risk checks
- MockBroker execution reports
- Portfolio / Account / PnL updates
- in-memory state with optional JSON/CSV output later

The MVP will not include FastAPI, database persistence, real broker connectivity, Redis/Kafka, ClickHouse, or C++ modules.

## Planned Directory Structure

```text
Trading-Infrastructure/
  README.md
  AGENTS.md
  pyproject.toml
  .gitignore
  .env.example

  docs/
    architecture.md
    research/
      open-source-comparison.md

  src/
    mini_trading/
      core/
      brokers/
      marketdata/
      strategies/
      app/
      config.py

  tests/
    unit/
    integration/
```

## Setup

Use a project-local virtual environment.

Recommended `uv` setup:

```powershell
uv python install 3.12
uv venv --python 3.12 .venv
uv pip install --python .venv\Scripts\python.exe -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest -q
```

Standard `venv` setup:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -e ".[dev]"
python -m pytest -q
```

If Python 3.11 is not installed, Python 3.12 is also supported.

## Roadmap

### Phase 0: Design And Foundation

- create safety and development rules
- compare open-source trading architecture ideas
- document project architecture
- create Python package skeleton
- add smoke test

### Phase 1: Core Models And Order State Machine

- define market data, order, fill, position, and account models
- implement order status transitions
- test valid and invalid transitions

Phase 1 establishes the core trading vocabulary. `Symbol`, `Quote`, `Trade`, `Order`, `Fill`, `Position`, `PnL`, and `AccountSnapshot` are typed domain objects. The order state machine protects the MVP lifecycle:

```text
CREATED -> SUBMITTED -> PARTIALLY_FILLED -> FILLED
CREATED / SUBMITTED -> REJECTED
CREATED / SUBMITTED / PARTIALLY_FILLED -> CANCELLED
```

`FILLED`, `CANCELLED`, and `REJECTED` are terminal states.

### Phase 2: Mini OMS, Risk Engine, Mock Broker

- create order manager
- implement pre-trade risk checks
- implement mock execution
- update portfolio, cash, and PnL from fills

Phase 2 connects the Phase 1 domain model into a deterministic local trading core. `RiskEngine` checks orders before execution, `MockBroker` simulates fills or broker rejects, `Portfolio` applies fills to cash/positions/PnL, and `OrderManager` orchestrates the flow.

Current supported Phase 2 behaviors:

- market order full fills
- limit order submitted/no-fill behavior when the limit condition is not met
- limit buy/sell fill checks
- risk rejection for kill switch, insufficient cash, max order notional, max position, oversell, and duplicate open orders
- broker rejection without portfolio update
- partial fill status and filled quantity tracking
- cancellation for submitted orders without portfolio update
- average-cost position updates
- realized and unrealized PnL calculation
- end-to-end buy/sell integration flow

### Phase 3: Event-Driven Chain

- connect mock market data to strategy, risk, OMS, broker, and portfolio
- add structured logging and error handling
- test the full trading flow

Phase 3 adds a deterministic local event-driven loop:

```text
MockMarketDataProvider
  -> PriceThresholdStrategy
  -> TradingEngine
  -> OrderManager
  -> RiskEngine
  -> MockBroker
  -> Portfolio
  -> AccountSnapshot
```

Current Phase 3 behavior:

- deterministic quote/trade market data events
- price-threshold strategy signals
- duplicate buy prevention while the strategy is already in position
- quote events ignored by the MVP strategy
- event-driven buy/sell integration flow
- tested CLI demo entry point

Run the demo from the project root without installing the package:

```powershell
$env:PYTHONPATH='src'
python -m mini_trading.app.cli_demo
```

Expected demo summary:

```text
events_processed=4
signals=2
orders=2
fills=2
cash=100120
equity=100120
realized_pnl=120
unrealized_pnl=0
```

### Phase 4: Simple Strategy And Replay

- implement price-threshold replay flow
- emit trade records and account snapshots
- add simple report output

Phase 4 adds replay reporting. The engine records an account snapshot after each market data event, and `ReplayReport` can export the run as JSON and CSV artifacts.

Report outputs:

- `summary.json`
- `orders.csv`
- `fills.csv`
- `account_snapshots.csv`

Run the demo and write reports:

```powershell
$env:PYTHONPATH='src'
python -m mini_trading.app.cli_demo reports/demo
```

This phase is intentionally lightweight. It is a replay/reporting layer for a deterministic MVP, not a full performance analytics platform.

### Phase 5: Persistence And Run History

- add SQLite persistence for orders, fills, account snapshots, and run summaries
- keep OMS, risk, broker, and portfolio logic independent from the database
- support deterministic replay auditing from persisted records

### Phase 6: Paper Trading Adapter

- optionally add Alpaca Paper integration
- keep MockBroker as the fully runnable default
- keep live trading disabled

### Phase 7: Engineering And Resume Polish

- add run examples, test coverage notes, and performance metrics
- write Chinese and English resume bullets
