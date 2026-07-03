# Mini Trading Infrastructure Design

## Objective

Build a resume-ready US equity Mini OMS project that demonstrates trading infrastructure engineering: market data events, strategy signals, pre-trade risk, order lifecycle management, mock execution, portfolio updates, and PnL accounting.

The project must remain mock-first. It must not perform live trading in the MVP.

## Confirmed MVP Decisions

- Runtime shape: CLI demo plus pytest tests.
- State: in-memory state first, with optional JSON/CSV output later.
- Market data: deterministic MockMarketDataProvider.
- Strategy: PriceThresholdStrategy for the MVP.
- Execution: MockBroker through a BrokerAdapter boundary.
- Account model: Portfolio / Account / PnL separated from OMS.
- PnL method: average cost for MVP.
- Orders: market and limit orders.
- Statuses: `CREATED`, `SUBMITTED`, `PARTIALLY_FILLED`, `FILLED`, `CANCELLED`, `REJECTED`.
- Python: project-local `.venv`, target Python 3.11, Python 3.12 allowed.

## Architecture

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

## Module Responsibilities

`marketdata` produces normalized quote/trade events. The MVP uses deterministic local events so tests are reproducible.

`strategies` converts market data into trade intent. Strategies must not mutate orders, cash, positions, or PnL.

`core.risk` rejects unsafe orders before execution. MVP rules include max order notional, max position, cash check, duplicate order guard, and kill switch.

`core.oms` owns order identity and lifecycle transitions.

`brokers` hides execution behind adapters. The MVP adapter is MockBroker; Alpaca Paper, IBKR, or FIX can be added later.

`core.portfolio` applies fills to positions and cash, then computes realized and unrealized PnL.

## Phase 0 Deliverables

- safety/development rules in `AGENTS.md`
- project metadata in `pyproject.toml`
- local environment example in `.env.example`
- architecture research in `docs/research/open-source-comparison.md`
- project architecture in `docs/architecture.md`
- README first version
- package skeleton under `src/mini_trading`
- smoke test proving safe defaults

## Deliberate MVP Exclusions

- live trading
- real broker connectivity
- FastAPI service
- database persistence
- Redis, Kafka, RabbitMQ, or ClickHouse
- C++ or Rust performance modules
- advanced order types
- fees, slippage, margin, short selling, options, and corporate actions
- claims about strategy profitability

## Success Criteria

Phase 0 is complete when the project has clear safety rules, documented architecture decisions, a minimal importable Python package, and a passing smoke test.

