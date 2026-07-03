# Architecture

## Goal

US Equity Mini Trading Infrastructure is a mock-first Mini OMS project for demonstrating trading-system engineering ability. It focuses on market data events, strategy signals, order management, risk checks, broker adaptation, fills, portfolio state, and PnL.

The MVP intentionally avoids real-money trading. All execution is mock by default.

## MVP Flow

```text
MockMarketDataProvider
        |
        v
PriceThresholdStrategy
        |
        v
RiskEngine
        |
        v
OrderManager
        |
        v
MockBroker
        |
        v
Portfolio / Account / PnL
```

Expanded event view:

```text
MarketDataEvent
  -> StrategySignal
  -> RiskCheckResult
  -> Order
  -> Fill
  -> AccountSnapshot
```

## Module Boundaries

### Market Data

`marketdata` produces normalized quote/trade events. The MVP uses deterministic mock data so tests and demos are reproducible. A future WebSocket provider should implement the same provider boundary.

Phase 3 implements `MockMarketDataProvider`. It can emit normalized `Quote` and `Trade` payloads wrapped in `MarketDataEvent`. The provider is deterministic and re-iterable, making integration tests stable.

### Strategy

`strategies` converts market data into trade intent. The MVP uses a price threshold strategy because it makes the OMS flow easy to test. Strategies must not directly mutate orders, cash, positions, or PnL.

Phase 3 implements `PriceThresholdStrategy`. It listens to trade events for one symbol, emits a market buy signal below the buy threshold, emits a market sell signal above the sell threshold after a buy, and ignores quote events. The strategy emits `StrategySignal` objects rather than orders.

### Risk Engine

`core.risk` validates orders before execution. MVP rules are max order notional, max position per symbol, cash check, duplicate order guard, and kill switch.

Phase 2 implements `RiskEngine` as a pre-trade gate. It receives an `Order`, an `AccountSnapshot`, a reference price, and open orders. If the check fails, the order becomes `REJECTED` before it reaches the broker adapter. This keeps invalid orders out of the execution path and preserves an internal rejection reason.

### Order Manager

`core.oms` owns order creation and status transitions. MVP order statuses are `CREATED`, `SUBMITTED`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, and `REJECTED`.

Phase 1 implements the status transition rules in `core.order_state`. Orders are immutable dataclasses, so a transition returns a new `Order` instance instead of mutating the existing one. This makes tests easier to reason about and avoids accidental hidden state changes.

Phase 2 adds `OrderManager`. It creates orders, calls `RiskEngine`, submits accepted orders to `BrokerAdapter`, applies broker fills to `Portfolio`, supports cancellation for cancellable orders, and stores order/fill history. Risk rejections do not call the broker; broker rejections and cancellations without fills do not update portfolio state.

### Broker Adapter

`brokers` translates internal order requests into execution reports. The MVP implements `MockBroker`; future adapters can target Alpaca Paper, IBKR, or FIX.

Phase 2 implements `MockBroker` with deterministic full-fill, partial-fill, no-fill limit order, and broker-reject scenarios. This is not a real matching engine. Its job is to provide controlled execution reports for testing the OMS and portfolio chain.

### Portfolio, Account, PnL

`core.portfolio` applies fills to positions and cash. MVP PnL uses average cost:

- buy: reduce cash, increase position quantity, update average cost
- sell: increase cash, reduce position quantity, update realized PnL
- mark-to-market: use latest market price for unrealized PnL and equity

Phase 2 implements `Portfolio.apply_fill()`, `Portfolio.mark_price()`, and `Portfolio.snapshot()`. Account state changes are fill-driven: creating or submitting an order does not change cash or positions.

### Persistence

`persistence` records completed trading runs after the core engine has produced a `TradingRunSummary`. It does not submit orders, run risk checks, execute fills, or mutate portfolio state.

Phase 5A implements `SQLiteRunStore` with the standard-library `sqlite3` module. The store persists:

- run summaries
- strategy signals
- final order records
- fills
- account snapshots
- per-snapshot positions

The dependency direction is one-way:

```text
TradingEngine -> TradingRunSummary -> SQLiteRunStore -> SQLite database
```

Core trading modules do not import `mini_trading.persistence`. This keeps OMS, risk, broker, strategy, and portfolio logic testable without a database.

## MVP In Scope

- Python package with `src` layout
- CLI demo as a thin application entry point
- deterministic mock market data
- price threshold strategy
- market and limit orders
- order state machine
- mock broker fills
- portfolio/account/PnL updates
- SQLite run-history persistence
- unit and integration tests
- safety defaults preventing live trading

## MVP Out Of Scope

- real broker connectivity
- live trading
- FastAPI service
- production database deployment
- Redis, Kafka, RabbitMQ, or ClickHouse
- C++ performance modules
- advanced matching engine
- advanced order types such as stop, IOC, FOK, OCO, or iceberg
- fees, slippage, margin, short selling, options, and corporate actions
- strategy profitability claims

## Future Extensions

1. Add FastAPI read-only endpoints for orders, fills, positions, and account state.
2. Add richer run-history queries and read-only persistence APIs.
3. Add Alpaca Paper adapters for paper market data and paper execution.
4. Add event transport with Redis Streams, RabbitMQ, or Kafka once the local event model is stable.
5. Add ClickHouse for high-volume historical market data.
6. Add C++ or Rust benchmark modules for order-book or latency experiments.

## Phase 3 Event Engine

`core.engine.TradingEngine` is the synchronous MVP event runner. It processes market data events in order, asks the strategy for a signal, sends each signal to `OrderManager`, and returns a `TradingRunSummary`.

This is event-driven in semantics but intentionally not yet asynchronous. The next natural extension is replacing the deterministic provider with an async WebSocket provider while keeping the strategy, OMS, risk, broker, and portfolio boundaries intact.

## Phase 4 Replay Reporting

Phase 4 records account snapshots after every processed market data event. This makes the run replayable: the project can explain how orders, fills, cash, positions, equity, and PnL changed over the event sequence.

`reports.replay.ReplayReport` serializes `TradingRunSummary` into:

- summary JSON
- orders CSV
- fills CSV
- account snapshots CSV

Reporting is intentionally separated from trading logic. `TradingEngine` produces a summary; `ReplayReport` serializes it; the CLI writes files. No database is introduced in this phase.

## Phase 5A SQLite Persistence

Phase 5A adds durable local run history. `SQLiteRunStore` receives a completed `TradingRunSummary` and writes one transaction containing run metadata, signals, orders, fills, account snapshots, and position snapshots.

Financial values are stored as text because the domain model uses `Decimal` and SQLite has no native fixed-precision decimal type. Storing values as `REAL` would introduce floating-point representation risk. Datetimes are stored as ISO-8601 text.

The SQLite schema is intentionally small and audit-oriented:

- `runs` stores final cash, equity, PnL, and row counts.
- `signals` stores strategy intent in event order.
- `orders` stores the final OMS order status and filled quantity.
- `fills` stores execution facts and notional.
- `account_snapshots` stores point-in-time account totals.
- `snapshot_positions` stores per-symbol holdings for each account snapshot.

The CLI can now write SQLite history:

```powershell
python -m mini_trading.app.cli_demo --sqlite reports/demo.sqlite
```

## Phase 5B Run History Query

Phase 5B adds a read-only CLI for inspecting persisted run history. It reuses `SQLiteRunStore` and prints deterministic CSV-style output for runs, orders, fills, account snapshots, and snapshot positions.

The query direction is:

```text
SQLite database -> SQLiteRunStore -> run_history CLI -> audit output
```

This layer remains outside the trading core. It does not submit orders, run strategies, mutate account state, or replay fills into a live `Portfolio`. Its purpose is post-run inspection.

Example commands:

```powershell
python -m mini_trading.app.run_history reports/demo.sqlite list-runs
python -m mini_trading.app.run_history reports/demo.sqlite show-run demo
python -m mini_trading.app.run_history reports/demo.sqlite orders demo
python -m mini_trading.app.run_history reports/demo.sqlite fills demo
python -m mini_trading.app.run_history reports/demo.sqlite snapshots demo
python -m mini_trading.app.run_history reports/demo.sqlite positions demo --snapshot-index 2
```

This read-only query boundary prepares the project for a future FastAPI read API: HTTP endpoints can wrap the same query semantics instead of reaching into OMS or Portfolio internals.

## Phase 6 FastAPI Read API

Phase 6 exposes the SQLite run-history read model through FastAPI. The API layer is intentionally thin:

```text
HTTP request -> FastAPI route -> SQLiteRunStore -> SQLite rows
```

It provides:

- `GET /health`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/orders`
- `GET /runs/{run_id}/fills`
- `GET /runs/{run_id}/snapshots`
- `GET /runs/{run_id}/positions`

The API is read-only. It does not call `TradingEngine`, `OrderManager`, `RiskEngine`, `MockBroker`, or `Portfolio` mutation methods. Missing run IDs return HTTP 404.

## Phase 7 Async Market Data Prototype

Phase 7 adds an async market-data boundary and deterministic async provider:

```text
AsyncMarketDataProvider -> AsyncTradingEngine -> Strategy -> OrderManager
```

`AsyncTradingEngine` consumes an async event stream while reusing the existing strategy, OMS, risk, broker, and portfolio modules. This proves the architecture can move toward real-time WebSocket-style ingestion without rewriting the trading core.

Real WebSocket connectivity, reconnect/backoff, and external credentials remain out of scope for this phase.
