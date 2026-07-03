# Resume And Interview Notes

This document is the long-term review notebook for the US Equity Mini Trading Infrastructure project. Update it whenever a new phase adds important behavior, architecture decisions, resume value, or interview talking points.

## Project Positioning

### One-Sentence Pitch

This project is a mock-first US equity Mini OMS trading infrastructure system. It is designed to demonstrate trading-system engineering ability: market data modeling, order lifecycle management, pre-trade risk, broker adapters, mock execution, portfolio/cash/PnL updates, and testable architecture.

### What This Project Is Not

- It is not a stock price prediction project.
- It is not a strategy profitability showcase.
- It is not investment advice.
- It does not perform live trading in the MVP.
- It defaults to mock execution and keeps paper/live trading clearly separated.

### Interview Opening Version

> I am building a mock-first US equity Mini OMS trading infrastructure project. The goal is to demonstrate execution and OMS engineering ability rather than strategy returns. The system is designed around a clear flow: market data events produce strategy signals, risk checks decide whether an order can be submitted, the OMS manages order lifecycle, a broker adapter returns fills, and the portfolio/account layer updates cash, positions, and PnL. So far I have completed the engineering foundation, core domain models, and order state machine.

## Current Project Status

### Completed: Phase 0

Phase 0 established the project foundation:

- `README.md` first version.
- `AGENTS.md` safety and development rules.
- `pyproject.toml` with Python package configuration.
- `.env.example` with safe mock defaults.
- `docs/research/open-source-comparison.md` comparing Lean, NautilusTrader, vn.py, OpenAlgo, quanttrader, IBKR examples, and event-driven backtesting ideas.
- `docs/architecture.md` describing module boundaries and MVP scope.
- Minimal importable Python package under `src/mini_trading`.
- Smoke test validating package import and safe default config.

### Completed: Phase 1

Phase 1 implemented core trading vocabulary and the order lifecycle state machine:

- `Symbol`
- `Quote`
- `Trade`
- `MarketDataEvent`
- `Order`
- `Fill`
- `Position`
- `PnL`
- `AccountSnapshot`
- `OrderSide`
- `OrderType`
- `OrderStatus`
- `MarketDataEventType`
- `VALID_ORDER_TRANSITIONS`
- `can_transition`
- `assert_transition`
- `transition_order`

Current verification result from the latest Phase 1 run:

```text
python -m pytest -q
17 passed
```

Environment note: the project target is Python 3.11 or 3.12, but the current local machine has only Python 3.10.10 available. Phase 1 tests passed on the available interpreter because the current code uses standard-library features compatible with it.

### Completed: Phase 2

Phase 2 connects the Phase 1 models into a deterministic local trading core:

- `RiskEngine`
- `RiskLimits`
- `RiskCheckResult`
- `Portfolio`
- `BrokerAdapter`
- `BrokerResult`
- `MockBroker`
- `OrderManager`
- `OrderSubmissionResult`

Implemented behavior:

- pre-trade risk checks before broker submission
- kill switch rejection
- max order notional rejection
- insufficient cash rejection
- max position rejection
- long-only oversell rejection
- duplicate open order rejection
- market order full fills
- limit buy/sell fill checks
- no-fill limit order remains `SUBMITTED`
- broker rejection without portfolio updates
- partial fill status and filled quantity tracking
- submitted order cancellation without portfolio updates
- fill-driven cash and position updates
- weighted average cost
- realized PnL on sell fills
- unrealized PnL through mark-to-market
- account snapshot equity calculation
- end-to-end buy/sell integration flow

Latest Phase 2 verification:

```text
python -m pytest -q
42 passed
```

### Completed: Phase 3

Phase 3 connects deterministic mock market data and a simple strategy into the Phase 2 trading core:

- `MarketDataProvider`
- `MockMarketDataProvider`
- `StrategySignal`
- `PriceThresholdStrategy`
- `TradingEngine`
- `TradingRunSummary`
- `run_demo()`

Implemented behavior:

- deterministic trade event stream
- quote event stream support
- price-threshold buy signal below buy threshold
- price-threshold sell signal above sell threshold after a buy
- duplicate buy prevention while the strategy is already in position
- quote events ignored by the MVP strategy
- event-driven routing from market data to strategy to OrderManager
- full buy/sell trading loop through RiskEngine, MockBroker, Portfolio, and AccountSnapshot
- deterministic CLI demo summary

Latest Phase 3 verification:

```text
python -m pytest -q
55 passed
```

Demo command from the project root without editable install:

```powershell
$env:PYTHONPATH='src'
python -m mini_trading.app.cli_demo
```

### Completed: Phase 4

Phase 4 adds replay reporting and exportable artifacts:

- account snapshots after each processed market data event
- `ReplayReport`
- JSON report serialization
- orders CSV
- fills CSV
- account snapshots CSV
- CLI report writer

Implemented behavior:

- mark-to-market account snapshots during event replay
- report dictionary suitable for inspection
- JSON summary with final cash, equity, and PnL
- CSV order records
- CSV fill records
- CSV account snapshot records
- demo report artifact writing

Latest Phase 4 verification:

```text
python -m pytest -q
62 passed
```

Demo command with reports:

```powershell
$env:PYTHONPATH='src'
python -m mini_trading.app.cli_demo reports/demo
```

### Completed: Phase 5A

Phase 5A adds SQLite run-history persistence:

- `SQLiteRunStore`
- `runs` table
- `signals` table
- `orders` table
- `fills` table
- `account_snapshots` table
- `snapshot_positions` table
- CLI `--sqlite` output option

Implemented behavior:

- save a completed `TradingRunSummary` into one SQLite transaction
- persist strategy signals, final order records, fills, account snapshots, and per-snapshot positions
- store `Decimal` values as exact text instead of SQLite `REAL`
- store datetimes as ISO-8601 text
- reject blank run IDs
- reject duplicate run IDs through SQLite primary keys
- preserve the core trading boundary: OMS, risk, broker, strategy, and portfolio do not import SQLite

Latest Phase 5A verification:

```text
python -m pytest -q
71 passed
```

Demo command with SQLite persistence:

```powershell
python -m mini_trading.app.cli_demo --sqlite reports/demo.sqlite
```

### Completed: Phase 5B

Phase 5B adds a read-only run-history query CLI:

- `mini_trading.app.run_history`
- `list-runs`
- `show-run`
- `orders`
- `fills`
- `snapshots`
- `positions`
- `positions --snapshot-index`

Implemented behavior:

- inspect persisted runs after the process exits
- print deterministic CSV-style output
- query final order states
- query fills and notional values
- query account snapshots
- query per-snapshot positions
- filter position rows by snapshot index
- keep query behavior outside the trading core

Latest Phase 5B verification:

```text
python -m pytest -q
78 passed
```

Run-history query examples:

```powershell
python -m mini_trading.app.run_history reports/demo.sqlite list-runs
python -m mini_trading.app.run_history reports/demo.sqlite show-run demo
python -m mini_trading.app.run_history reports/demo.sqlite positions demo --snapshot-index 2
```

## Architecture Story

The intended MVP flow is:

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

### Key Boundary Principle

Each module should have one job:

- Strategy generates intent. It does not mutate orders or accounts.
- RiskEngine decides whether an order is allowed before execution.
- OMS manages order identity, lifecycle, and status consistency.
- BrokerAdapter translates internal orders into execution requests and external reports into internal fills/status updates.
- Portfolio applies fills to cash, positions, average cost, and PnL.

## Key Design Concepts

### OrderStatus

Code: `src/mini_trading/core/enums.py`

`OrderStatus` represents the lifecycle stage of an order:

- `CREATED`: the order exists inside the system but has not been submitted to a broker or execution adapter.
- `SUBMITTED`: the order passed internal checks and was submitted to the execution side.
- `PARTIALLY_FILLED`: part of the order quantity was executed, but some quantity remains.
- `FILLED`: the full order quantity was executed. This is a terminal state.
- `CANCELLED`: the remaining quantity was cancelled. This is a terminal state. A cancelled order may still have previous fills.
- `REJECTED`: the order was refused by internal risk checks or by the broker/exchange. This is a terminal state.

Important interview point:

> Even if a market order fills quickly, the OMS should still preserve `CREATED -> SUBMITTED -> FILLED` because `SUBMITTED` records that the order left internal intent and entered execution.

### Order State Machine

Code: `src/mini_trading/core/order_state.py`

The allowed MVP transitions are:

```text
CREATED -> SUBMITTED
CREATED -> CANCELLED
CREATED -> REJECTED

SUBMITTED -> PARTIALLY_FILLED
SUBMITTED -> FILLED
SUBMITTED -> CANCELLED
SUBMITTED -> REJECTED

PARTIALLY_FILLED -> FILLED
PARTIALLY_FILLED -> CANCELLED
```

Terminal states:

```text
FILLED
CANCELLED
REJECTED
```

These cannot transition further. This protects OMS consistency and prevents impossible states such as `FILLED -> SUBMITTED` or `CANCELLED -> FILLED`.

### Order vs Fill

Code: `src/mini_trading/core/models.py`

`Order` means trading intent:

```text
I want to buy 100 shares of AAPL.
```

`Fill` means actual execution result:

```text
40 shares of AAPL were bought at 180.25.
```

Relationship:

```text
1 Order -> 0 Fills
1 Order -> 1 Fill
1 Order -> many Fills
```

Why they must be separate:

- An order may never execute.
- An order may partially execute.
- An order may execute across multiple prices.
- An order may partially fill and then cancel.
- Portfolio and PnL should update from `Fill`, not from the original `Order`.

Interview answer:

> I separate Order and Fill because Order is intent and Fill is execution. A single order can have zero, one, or many fills. Cash, position, and PnL updates must be based on fills because only actual execution changes the account.

### RiskEngine And Pre-Trade Risk

Code: `src/mini_trading/core/risk.py`

`RiskEngine` is the pre-trade gate. It checks an order before it reaches the broker adapter.

Current MVP risk rules:

- kill switch rejects every order
- max order notional
- cash check for buy orders
- max position quantity for buy orders
- long-only sell quantity check
- duplicate open order check

Interview answer:

> Pre-trade risk means checking an order before execution. In my project, OrderManager calls RiskEngine before broker submission. If the order fails risk, it becomes `REJECTED`, the broker is not called, and portfolio state remains unchanged. This keeps unsafe or invalid orders out of the execution path.

### MockBroker

Code: `src/mini_trading/brokers/mock.py`

`MockBroker` simulates execution reports without connecting to a real broker.

It supports:

- market order full fill
- limit buy fill when market price is at or below limit price
- limit sell fill when market price is at or above limit price
- submitted/no-fill result when a limit condition is not met
- deterministic partial fill mode
- deterministic broker reject mode

Interview answer:

> MockBroker is not meant to simulate the full market microstructure. Its job is to provide deterministic execution reports so I can test OMS state transitions, partial fills, rejects, and portfolio updates without real-money risk or external API dependencies.

### OrderManager

Code: `src/mini_trading/core/oms.py`

`OrderManager` orchestrates the Phase 2 trading core:

```text
create Order
  -> RiskEngine.check_order
  -> transition CREATED to SUBMITTED
  -> BrokerAdapter.submit_order
  -> update Order status and filled quantity
  -> apply Fill to Portfolio
```

Important invariants:

- risk rejection does not call broker
- broker rejection does not update portfolio
- no-fill limit orders remain submitted
- submitted or partially filled orders can be cancelled through the state machine
- only fills change cash, positions, and PnL

Interview answer:

> OrderManager is the coordination layer. It does not calculate PnL itself and it does not simulate broker execution itself. It delegates risk to RiskEngine, execution to BrokerAdapter, and account updates to Portfolio.

### Quote vs Trade

`Quote` is current market quotation:

```text
bid = highest price buyers are willing to pay
ask = lowest price sellers are willing to accept
spread = ask - bid
```

`Trade` is actual transaction:

```text
price = executed price
quantity = executed size
```

Why they must be separate:

- A quote update does not mean a trade occurred.
- A trade may happen without a new quote update.
- Market buy simulation usually references ask.
- Market sell simulation usually references bid.
- Last trade price is not always the same as current tradable quote.

Interview answer:

> Quote and Trade are both market data, but they have different meanings. Quote represents available bid/ask liquidity; Trade represents actual execution in the market. Keeping them separate helps future WebSocket market data adapters normalize quote and trade channels correctly.

### MockMarketDataProvider

Code: `src/mini_trading/marketdata/mock.py`

`MockMarketDataProvider` is a deterministic source of normalized market data events. It can emit `Trade` and `Quote` events and is re-iterable, which makes tests and demos reproducible.

Interview answer:

> I use MockMarketDataProvider to simulate a market data stream without depending on a live API or WebSocket. It produces the same normalized MarketDataEvent objects that future real providers should emit, so the downstream strategy and OMS flow do not care where the data came from.

### StrategySignal And PriceThresholdStrategy

Code: `src/mini_trading/strategies/base.py` and `src/mini_trading/strategies/threshold.py`

`StrategySignal` represents trade intent, not an order. It contains symbol, side, order type, quantity, and a reference price.

`PriceThresholdStrategy`:

- listens to trade events
- ignores quote events
- buys when price is below `buy_below`
- sells when price is above `sell_above` after a buy
- avoids repeated buy signals while already in position
- keeps signal state separate from confirmed execution state
- updates confirmed position state through `on_order_result()`

Interview answer:

> The threshold strategy is deliberately simple. It is not meant to prove alpha. Its job is to generate deterministic signals so the project can demonstrate the infrastructure chain: market data -> signal -> risk -> order -> broker -> fill -> portfolio.

Important review note:

> A strategy signal is not a fill. The strategy should not assume it has a position just because it emitted a buy signal. It now waits for execution feedback from OrderManager before updating confirmed position state.

### TradingEngine

Code: `src/mini_trading/core/engine.py`

`TradingEngine` is the MVP event runner:

```text
MarketDataEvent
  -> Strategy.on_event
  -> StrategySignal
  -> OrderManager.submit_order
  -> TradingRunSummary
```

Interview answer:

> TradingEngine is event-driven in semantics: it processes a sequence of market data events and reacts to each event. It remains synchronous in the MVP so tests are deterministic. Later, the market data provider can become an async WebSocket source without changing strategy, OMS, risk, broker, or portfolio boundaries.

### ReplayReport

Code: `src/mini_trading/reports/replay.py`

`ReplayReport` converts a `TradingRunSummary` into reviewable artifacts:

- `summary.json`
- `orders.csv`
- `fills.csv`
- `account_snapshots.csv`

Interview answer:

> Phase 4 makes the system replayable. Instead of only printing final PnL, the engine records account snapshots after each market data event, and the reporting layer exports orders, fills, and account state changes. This helps explain how the account moved from event to event.

### SQLiteRunStore And Persistence Boundary

Code: `src/mini_trading/persistence/sqlite.py`

`SQLiteRunStore` stores completed trading runs. It receives a `TradingRunSummary` after `TradingEngine.run()` finishes and writes the run to SQLite.

It persists:

- run-level counts and final account values
- strategy signals
- final order states
- fills
- account snapshots
- per-snapshot positions

Important design point:

```text
TradingEngine -> TradingRunSummary -> SQLiteRunStore -> SQLite
```

The dependency does not point backward. `core.engine`, `core.oms`, `core.risk`, `brokers`, `strategies`, and `portfolio` do not import SQLite. This keeps trading logic testable and prevents persistence details from leaking into order lifecycle logic.

Financial values are stored as text:

```text
Decimal("100120") -> "100120"
```

Reason:

- SQLite has no native fixed-precision decimal type.
- SQLite `REAL` is floating point.
- Financial audit rows should preserve exact values.

Interview answer:

> I added SQLite as a persistence boundary rather than as part of the trading core. The engine computes a TradingRunSummary in memory; SQLiteRunStore records that result transactionally. I store Decimal values as text to avoid floating-point drift, and I persist position snapshots so PnL can be explained symbol by symbol.

### Run History Query CLI

Code: `src/mini_trading/app/run_history.py`

The run-history CLI is a read-only audit interface over SQLite persistence. It lets a user inspect saved runs without rerunning the strategy or mutating portfolio state.

Supported commands:

- `list-runs`
- `show-run`
- `orders`
- `fills`
- `snapshots`
- `positions`
- `positions --snapshot-index`

Dependency direction:

```text
SQLite database -> SQLiteRunStore -> run_history CLI -> CSV-style output
```

Interview answer:

> Phase 5B turns persistence into an audit workflow. After a demo run is saved, I can query the run summary, orders, fills, account snapshots, and per-snapshot positions from the command line. This remains read-only and outside the trading core, which makes it a natural precursor to a future FastAPI read API.

### Position, AccountSnapshot, And PnL

`Position` represents holdings for one symbol:

- `quantity`: current shares held.
- `average_cost`: average acquisition cost.
- `last_price`: latest mark price.
- `market_value = quantity * last_price`
- `unrealized_pnl = (last_price - average_cost) * quantity`

`PnL` separates:

- `realized`: profit/loss from sold or closed quantity.
- `unrealized`: mark-to-market profit/loss on open positions.

`AccountSnapshot` aggregates:

- `cash`
- `positions`
- `pnl`
- `gross_market_value`
- `equity = cash + gross_market_value`

Interview answer:

> Position tracks what the account currently holds. PnL explains profit and loss. AccountSnapshot combines cash, positions, and PnL into a point-in-time account view. Cash and equity are not the same: cash can decrease when buying stock, while equity includes both cash and current position value.

Phase 2 adds fill-driven portfolio updates. Buy fills reduce cash and increase position quantity. Additional buys update average cost using weighted average cost. Sell fills increase cash, reduce position quantity, and realize PnL based on sell price minus average cost.

## Python Engineering Choices

### Decimal

Prices, quantities, notional, cash, and PnL use `Decimal` instead of `float`.

Reason:

- `float` is binary floating point and cannot exactly represent many decimal values.
- Financial calculations should be stable and explainable.
- Tests for notional, cash, and PnL are easier to make deterministic.

Balanced answer:

> Decimal is good for MVP correctness and clarity. For low-latency hot paths, fixed-point integers such as ticks or cents may be better.

### Enum

`OrderSide`, `OrderType`, `OrderStatus`, and `MarketDataEventType` use `str, Enum`.

Reason:

- They represent finite domain vocabularies.
- They prevent magic strings and spelling drift.
- String enum values are friendly for logs, JSON APIs, and future database fields.

### dataclass

Core models use `dataclass` because they are typed domain objects with clear fields.

Compared with `dict`, dataclasses provide:

- explicit fields
- clearer type expectations
- better test readability
- easier refactoring
- centralized validation through `__post_init__`

### frozen=True

Core domain objects are frozen dataclasses.

Reason:

- Avoid hidden mutation.
- Force order status changes through state machine functions.
- Make tests easier to reason about.
- Prepare for future audit/event logging.

Important trade-off:

> Immutable objects create new instances on update. This is acceptable for MVP correctness and clarity, but hot paths can be optimized later if needed.

### Why Not Pydantic In Core

Pydantic is useful at system boundaries:

- API requests/responses
- JSON parsing
- configuration validation

The core domain currently uses standard-library dataclasses so trading logic does not depend on FastAPI or serialization frameworks. Future FastAPI schemas can convert to and from core dataclasses.

### Why `src/` Layout

The project uses:

```text
src/mini_trading
tests
docs
```

Reason:

- separates source from tests and docs
- is closer to installable package structure
- helps avoid accidental imports from the project root

## Testing And Quality Notes

Current tests prove domain invariants rather than merely chasing coverage.

### Smoke Test

`tests/unit/test_package_smoke.py` verifies:

- package imports
- `__version__`
- default trading mode is `mock`
- live trading is disabled

Interview point:

> Safety defaults are executable checks, not only README text.

### Core Model Tests

`tests/unit/test_core_models.py` verifies:

- symbol normalization
- blank ticker rejection
- positive quote bid/ask
- bid not above ask
- quote spread
- positive trade price and quantity
- trade notional
- market data event symbol forwarding
- market order default `CREATED` state
- limit order requires limit price
- fill notional
- position market value
- position unrealized PnL
- account gross market value
- account equity

### Order State Tests

`tests/unit/test_order_state.py` verifies:

- valid transitions from `CREATED`
- valid transitions from `SUBMITTED`
- valid transitions from `PARTIALLY_FILLED`
- terminal states cannot transition
- invalid transitions raise `InvalidOrderTransition`
- `transition_order` returns a new immutable order instead of mutating the original

### Phase 2 Tests

Phase 2 adds tests for:

- RiskEngine approval and rejection paths
- kill switch
- max notional
- insufficient cash
- max position
- oversell rejection
- duplicate open orders
- Portfolio buy/sell fill updates
- weighted average cost
- realized and unrealized PnL
- MockBroker full fill, no-fill limit, partial fill, and reject behavior
- OrderManager risk rejection, broker rejection, limit submitted state, partial fill state, and full fill state
- OrderManager cancellation for submitted orders
- end-to-end buy/sell order execution flow

### Phase 3 Tests

Phase 3 adds tests for:

- deterministic mock trade streams
- quote event wrapping
- provider re-iterability
- threshold buy/sell signals
- quote events ignored by strategy
- duplicate buy prevention while already in position
- rejected buy signal recovery
- event-driven buy/sell flow from market data to account snapshot
- quote-only stream producing no trades
- deterministic CLI demo summary

### Phase 4 Tests

Phase 4 adds tests for:

- account snapshots after each event
- mark-to-market equity changes without new orders
- report dictionary conversion
- JSON report serialization
- orders CSV
- fills CSV
- account snapshots CSV
- CLI report artifact writing

### Phase 5A Tests

Phase 5A adds tests for:

- SQLite schema initialization
- persisted run counts and final account values
- persisted strategy signals
- persisted final order records
- persisted fills and notional values
- persisted account snapshots
- persisted per-snapshot positions
- exact `Decimal` string storage
- blank run ID rejection
- duplicate run ID rejection
- CLI SQLite database writing
- existing JSON/CSV CLI output compatibility

### Phase 5B Tests

Phase 5B adds tests for:

- listing saved runs
- showing one run summary
- querying persisted orders
- querying persisted fills
- querying account snapshots
- querying per-snapshot positions
- filtering positions by snapshot index
- preserving deterministic CSV-style CLI output

Testing interview answer:

> I test business invariants: order quantity must be positive, limit orders require limit price, quote bid cannot exceed ask, fills compute notional correctly, and order states cannot move through impossible transitions. The tests protect trading-system consistency, not just code coverage.

## High-Frequency Interview Questions

### Financial And Trading Basics

#### What is ticker or symbol?

Ticker or symbol is the tradable instrument identifier, such as `AAPL` or `MSFT`. In the system, it links market data, orders, fills, and positions.

#### What is quote vs trade?

Quote is bid/ask quotation. Trade is actual transaction. Quote says what the market is currently offering; trade says what actually happened.

#### What are bid, ask, and spread?

Bid is the highest price buyers are willing to pay. Ask is the lowest price sellers are willing to accept. Spread is `ask - bid`, often interpreted as an immediate trading cost and liquidity signal.

#### What is market order vs limit order?

Market order prioritizes execution speed and does not specify a price. Limit order specifies a worst acceptable price. Buy limit orders should not execute above limit price; sell limit orders should not execute below limit price.

#### What is partial fill?

Partial fill means only part of the order quantity executed. The remaining quantity may continue working or be cancelled.

#### What is cancelled vs rejected?

Cancelled means the remaining order quantity is stopped. It may already have previous fills. Rejected means the order was refused by risk, broker, or exchange and should not produce fills.

#### What is pre-trade risk?

Pre-trade risk checks an order before execution. Examples include max order notional, cash check, max position, duplicate order guard, and kill switch.

#### How does your RiskEngine decide whether to reject an order?

It checks kill switch first, then order notional, cash sufficiency for buys, max position for buys, long-only sell quantity, and duplicate open orders. If a check fails, it returns a rejected `RiskCheckResult`; OrderManager then marks the order `REJECTED` without calling the broker.

### OMS And Execution Design

#### Why do we need an OMS?

OMS manages order identity, lifecycle, status transitions, execution reports, and consistency across risk, broker, and portfolio modules. It is more than a buy/sell function.

#### Why should strategy not call broker directly?

Strategy should only generate intent. Direct broker calls bypass risk checks, OMS state tracking, logging, and safety controls.

#### Why need BrokerAdapter?

BrokerAdapter isolates external broker differences. OMS should work with internal `Order` and `Fill` models, while adapters translate to/from Alpaca, IBKR, FIX, or MockBroker formats.

#### Why start with MockBroker?

MockBroker gives deterministic, local, safe testing of filled, partial fill, rejected, and cancelled scenarios without API keys, network issues, market hours, or real-money risk.

#### What does OrderManager do now?

OrderManager creates orders, performs risk checks, submits accepted orders to the broker adapter, applies fills to the portfolio, and stores order/fill history. It coordinates modules but does not own all business logic.

#### Why event-driven design?

Trading systems react to events: market data, signals, orders, fills, cancels, rejects, and account updates. Event-driven design mirrors real trading flow and prepares the project for WebSocket and message-queue extensions.

#### Is Phase 3 already a real-time WebSocket system?

No. Phase 3 is event-driven in architecture but uses deterministic local events. This is intentional: it proves the event semantics and trading chain first. A later WebSocket provider can implement the same `MarketDataProvider` boundary.

#### What does Phase 4 reporting prove?

It proves the trading run is inspectable and replayable. The report records orders, fills, and account snapshots so a reviewer can trace how market events led to signals, fills, cash changes, equity changes, and PnL.

#### Why use a simple price-threshold strategy?

Because the project is about trading infrastructure, not alpha research. A threshold strategy is easy to reason about and test, so it is a good signal generator for proving the OMS, risk, broker, and portfolio chain.

#### Why isolate mock, paper, and live?

They have different risk levels. Mock is local, paper uses external simulated trading, and live uses real money. Live must stay disabled by default, with explicit endpoint and credential separation.

### Python Engineering

#### Why not FastAPI yet?

FastAPI is useful as an interface layer after the core is stable. The MVP first focuses on OMS logic, risk, broker simulation, and account updates. API endpoints should be thin adapters, not places where trading logic lives.

#### Why introduce SQLite in Phase 5A instead of earlier?

The domain model needed to stabilize first. If persistence came before `Order`, `Fill`, `AccountSnapshot`, and `TradingRunSummary` were clear, the schema would likely mirror unstable implementation details. Phase 5A introduces SQLite after the in-memory trading chain and replay reports are stable, so the database records well-defined trading facts rather than driving the business logic.

#### Why SQLite instead of PostgreSQL or an ORM?

SQLite is enough for local deterministic run history. It is standard-library friendly, requires no service setup, and makes the project easy to run in interviews or demos. PostgreSQL or SQLAlchemy can be added later if the project needs multi-user access, migrations, richer querying, or production deployment.

#### Why store Decimal values as text?

SQLite `REAL` uses floating-point representation, which is not ideal for financial audit values. The project uses `Decimal` in the domain model and stores those values as strings such as `"100120"` or `"99"` so persisted rows preserve exact values.

#### What does the run-history query layer add?

It makes persisted trading runs inspectable after the process exits. Instead of only saving rows, Phase 5B adds commands to query run summaries, orders, fills, account snapshots, and per-snapshot positions. This is an audit layer, not a trading layer.

#### Why is the query layer read-only?

Historical trading records should not be casually mutated by inspection tools. Keeping the query CLI read-only preserves the idea that orders, fills, and account snapshots are facts produced by the trading engine and persisted by the store.

#### How does this prepare for FastAPI later?

A future FastAPI service can wrap the same query semantics: list runs, show a run, list orders, list fills, and show snapshots. Because Phase 5B already keeps query behavior separate from OMS and Portfolio logic, the API layer can remain thin.

#### Why not Kafka or Redis yet?

First define event semantics locally. After `MarketDataEvent`, `OrderEvent`, `FillEvent`, and account events are stable, choose transport. Redis Streams, RabbitMQ, or Kafka should solve a clear event-flow need, not decorate the MVP.

#### How would asyncio fit later?

Use async at I/O boundaries: WebSocket market data provider and broker adapters. Keep core domain logic synchronous and pure for easy testing.

### Testing And Reliability

#### How do you test state machine behavior?

Test valid transitions, invalid transitions, terminal states, and immutable transition behavior.

#### How would you test partial fill?

Create a 100-share order, have MockBroker return a 40-share fill, assert `PARTIALLY_FILLED`, remaining 60, and portfolio updated for 40 only. Then return the remaining 60 and assert `FILLED`.

This is now partially implemented in Phase 2: MockBroker can return a deterministic partial fill, and OrderManager records `PARTIALLY_FILLED`, updates filled quantity, and applies only the filled quantity to Portfolio. OrderManager can also cancel cancellable orders through the same state machine.

#### How would you test rejected order?

Test both internal risk rejection and broker rejection. Rejected orders should not create fills or update portfolio.

#### How would you test WebSocket reconnect?

Use a fake async source or fake server to simulate disconnect and reconnect. Verify retry/backoff behavior, error logging, recovery, and no duplicate event processing.

#### How would you measure latency?

Use `time.perf_counter_ns()` around stages such as market event handling, risk check, order processing, broker simulation, and portfolio update. Report throughput and p50/p95/p99 latency.

### Project Boundary And Extensions

#### What is missing now?

The current project has domain models and order state machine. It does not yet have OrderManager, RiskEngine, MockBroker, Portfolio apply-fill logic, or full trading flow.

#### Why not build everything at once?

Trading systems have many moving parts. Incremental phases keep each milestone runnable and testable, and prevent API/database/infrastructure work from hiding core OMS logic.

#### How to extend to Alpaca Paper?

Implement `AlpacaPaperBrokerAdapter` behind the same internal broker boundary. Translate internal `Order` to Alpaca requests, translate Alpaca responses/execution reports to internal `OrderStatus` and `Fill`. Use environment variables and paper endpoints only.

#### How to extend to IBKR or FIX?

Add adapters that handle session, reconnect, external/internal order ID mapping, execution reports, rejects, and reconciliation. Core OMS should remain independent from protocol-specific fields.

#### How to extend to C++?

Keep Python for orchestration and domain flow. Add C++ only for performance-sensitive modules with clear boundaries, such as order book, matching engine, fixed-point calculations, or latency benchmarks.

## Resume Bullets

### Current Phase 1 Version

Chinese:

> 设计美股 Mini OMS 模拟交易系统核心架构，完成 Quote/Trade/Order/Fill/Position/PnL/AccountSnapshot 等领域模型与订单状态机，基于 Decimal、Enum、不可变 dataclass 提升金额计算准确性、状态一致性和可测试性，并使用 pytest 覆盖订单非法流转、行情/成交模型校验和账户权益计算。

English:

> Designed the core domain model and order lifecycle state machine for a mock-first US equity Mini OMS, modeling Quote, Trade, Order, Fill, Position, PnL, and AccountSnapshot with Decimal, Enum, and immutable dataclasses, with pytest coverage for invalid state transitions, market data validation, fill notional, position valuation, and account equity.

### Phase 2 Completed Version

Chinese:

> 基于 Python 构建 mock-first 美股 Mini OMS 模拟交易系统，实现 Market/Limit 订单、订单状态机、Pre-trade Risk、Mock Broker 成交回报、持仓/现金/PnL 更新，并通过 pytest 覆盖拒单、部分成交、撤单和账户更新等核心场景。

English:

> Built a mock-first US equity Mini OMS in Python with market/limit orders, an order lifecycle state machine, pre-trade risk checks, mock broker execution reports, and portfolio/cash/PnL updates, with pytest coverage for rejections, partial fills, cancellations, and account state transitions.

### Phase 3 Completed Version

Chinese:

> 基于 Python 构建 mock-first 美股 Mini OMS 模拟交易系统，实现确定性 Mock 行情流、Price Threshold 策略信号、Pre-trade Risk、订单状态机、Mock Broker 成交回报、持仓/现金/PnL 更新，并通过 pytest 覆盖行情事件、策略信号、拒单、部分成交、撤单和端到端交易闭环。

English:

> Built a mock-first US equity Mini OMS in Python with deterministic market data events, price-threshold strategy signals, pre-trade risk checks, order lifecycle management, mock broker execution, and portfolio/cash/PnL updates, with pytest coverage for market events, signals, rejections, partial fills, cancellations, and end-to-end trading flow.

### Phase 4 Completed Version

Chinese:

> 基于 Python 构建 mock-first 美股 Mini OMS 模拟交易系统，支持确定性行情回放、阈值策略信号、风控校验、Mock Broker 成交回报、持仓/现金/PnL 更新，并导出 orders、fills、account snapshots 和 summary JSON/CSV 报告，用于复盘订单生命周期、成交与账户权益变化。

English:

> Built a mock-first US equity Mini OMS in Python with deterministic replay, threshold strategy signals, pre-trade risk checks, mock broker execution, portfolio/cash/PnL updates, and JSON/CSV reports for orders, fills, account snapshots, and final run summary.

### Phase 5A Completed Version

Chinese:

> 基于 Python 构建 mock-first 美股 Mini OMS 模拟交易系统，新增 SQLite run-history 持久化层，将策略信号、订单、成交、账户快照和逐快照持仓以事务方式保存为可审计记录，并保持 OMS、风控、Broker Adapter 和 Portfolio 核心逻辑与数据库解耦。

English:

> Built a mock-first US equity Mini OMS in Python with SQLite run-history persistence, transactionally storing strategy signals, orders, fills, account snapshots, and per-snapshot positions while keeping OMS, risk, broker, and portfolio logic independent from the database.

### Phase 5B Completed Version

Chinese:

> 基于 Python 构建 mock-first 美股 Mini OMS 模拟交易系统，新增 SQLite run-history 只读查询 CLI，支持查看历史 run、订单、成交、账户快照和逐快照持仓，为后续 FastAPI 只读接口和交易审计复盘打下基础。

English:

> Built a read-only SQLite run-history query CLI for a mock-first US equity Mini OMS, enabling inspection of historical runs, orders, fills, account snapshots, and per-snapshot positions while preserving a clean boundary from trading-core logic.

### Final Target Version

Chinese:

> 基于 Python asyncio + WebSocket 构建美股实时行情接入模块，设计 Mini OMS 订单管理系统，实现 Market/Limit 订单、订单状态机、风控校验、成交回报、持仓与 PnL 更新；通过 Mock Broker 与可选 Alpaca Paper Trading API 完成模拟交易闭环，并针对行情处理延迟、订单处理耗时、异常重连和拒单场景进行日志监控与稳定性优化。

English:

> Built a mock-first US equity mini trading infrastructure in Python, including market data events, a Mini OMS, order lifecycle state machine, pre-trade risk checks, mock broker execution, portfolio/cash/PnL updates, and pytest coverage for rejection, partial fills, cancellations, and account state transitions.

## Update Rules For This Document

Update this file after each meaningful project change:

- New phase completed.
- New module added.
- Important design decision changed.
- New financial concept introduced.
- New interview question appears.
- Resume bullet can be strengthened.
- Tests or verification strategy changes.
- Safety boundary changes.

Suggested update sections:

- Current Project Status
- Key Design Concepts
- High-Frequency Interview Questions
- Resume Bullets
- Next Development Targets

## Next Development Targets

### Completed Review: Phase 0-4 Architecture And Cleanup

Review document: `docs/reviews/2026-07-03-phase-0-4-review.md`

Key cleanup completed:

- fixed strategy state synchronization so signal generation does not equal execution confirmation
- added regression coverage for rejected buy signal recovery
- recorded remaining engineering risks before persistence work

Completed setup work:

- installed Python 3.12.13 through `uv`
- created project-local `.venv`
- initialized git and committed the Phase 0-4 baseline

### Completed Phase 2: Mini OMS, RiskEngine, MockBroker, Portfolio

Goal achieved: the Phase 1 models now form a local executable trading core.

Planned modules:

- `src/mini_trading/core/risk.py`
- `src/mini_trading/core/oms.py`
- `src/mini_trading/core/portfolio.py`
- `src/mini_trading/brokers/base.py`
- `src/mini_trading/brokers/mock.py`

Planned tests:

- `tests/unit/test_risk.py`
- `tests/unit/test_portfolio.py`
- `tests/unit/test_mock_broker.py`
- `tests/unit/test_oms.py`
- `tests/integration/test_order_execution_flow.py`

Implemented behaviors:

- create market and limit orders
- run pre-trade risk before broker submission
- reject unsafe orders
- submit safe orders to MockBroker
- simulate full fills
- simulate partial fills
- simulate broker rejects
- cancel submitted orders
- update order filled quantity and status
- update cash and position from fills
- compute average cost
- compute realized and unrealized PnL
- keep all behavior mock-first and deterministic

### Completed Phase 3: Event-Driven Trading Flow

Goal achieved: mock market data, strategy, risk, OMS, broker, and portfolio now run in one deterministic local event loop.

Target flow:

```text
MockMarketDataProvider
  -> PriceThresholdStrategy
  -> RiskEngine
  -> OrderManager
  -> MockBroker
  -> Portfolio
  -> AccountSnapshot
```

Implemented behaviors:

- deterministic market data stream
- threshold-based buy/sell signal
- full trading loop integration test
- deterministic CLI demo summary

### Completed Phase 4: Replay And Reporting

Goal achieved: the trading chain can be replayed and exported as JSON/CSV reports.

Implemented outputs:

- trade records
- order records
- position changes
- account snapshots
- simple JSON/CSV report

### Completed Phase 5A: SQLite Persistence

Goal achieved: completed trading runs can be persisted as local SQLite audit records.

Implemented modules:

- `src/mini_trading/persistence/sqlite.py`
- `src/mini_trading/persistence/__init__.py`

Implemented outputs:

- run summary rows
- signal rows
- order rows
- fill rows
- account snapshot rows
- snapshot position rows

Key boundary:

```text
TradingEngine -> TradingRunSummary -> SQLiteRunStore -> SQLite
```

The database stores results after the trading core finishes; it does not drive OMS state transitions, risk checks, broker execution, or PnL calculation.

### Completed Phase 5B: Run History Query CLI

Goal achieved: persisted trading runs can be inspected through a read-only CLI.

Implemented module:

- `src/mini_trading/app/run_history.py`

Implemented commands:

- `list-runs`
- `show-run`
- `orders`
- `fills`
- `snapshots`
- `positions`
- `positions --snapshot-index`

Key boundary:

```text
SQLite database -> SQLiteRunStore -> run_history CLI -> audit output
```

This prepares the project for a future read-only FastAPI layer.

### Later Extensions

- FastAPI read-only query layer
- richer persistence query APIs
- Alpaca Paper adapter
- WebSocket market data provider
- Redis/RabbitMQ/Kafka event transport
- ClickHouse market data or latency analytics
- C++ or Rust performance module for order book or latency benchmark
