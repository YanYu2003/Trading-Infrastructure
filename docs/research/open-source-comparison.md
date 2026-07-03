# Open-Source Trading Architecture Comparison

This note compares architecture ideas from mature trading and backtesting projects before this project implements its own smaller Mini OMS. The goal is not to copy code. The goal is to borrow proven boundaries: event flow, broker adapters, order tracking, risk checks, market data handling, and backtest/paper/live consistency.

## Sources Reviewed

- [QuantConnect Lean](https://github.com/QuantConnect/Lean) and [QuantConnect Algorithm Engine docs](https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/algorithm-engine)
- [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) and [NautilusTrader architecture docs](https://nautilustrader.io/docs/latest/concepts/architecture/)
- [vn.py / VeighNa](https://github.com/vnpy/vnpy) and [VeighNa user docs](https://www.vnpy.com/docs/)
- [OpenAlgo](https://github.com/marketcalls/openalgo)
- [quanttrader](https://github.com/letianzj/quanttrader)
- [InteractiveBrokers-Algo-Trading-API](https://github.com/rediar/InteractiveBrokers-Algo-Trading-API)
- [QuantStart event-driven backtesting series](https://www.quantstart.com/articles/Event-Driven-Backtesting-with-Python-Part-V/) and [PyEventBT architecture notes](https://pyeventbt.com/)

## Comparison

| Project | Relevant Architecture Ideas | What This Project Borrows | What This Project Avoids In MVP |
| --- | --- | --- | --- |
| QuantConnect Lean | Event-driven algorithm engine, modular components, backtest and live trading in one platform, broker/data provider separation. | Event-driven thinking, pluggable boundaries, clear distinction between algorithm logic and execution infrastructure. | Full multi-asset engine, cloud/local workflow, complex brokerage coverage, optimizer/research platform. |
| NautilusTrader | Deterministic event-driven runtime, strong domain model, adapters for venues/data providers, research-to-live parity, performance-oriented core. | Adapter boundaries, deterministic mock flow, domain-first design, future path to stronger event bus and performance modules. | Rust engine, nanosecond precision, complex order types, multi-venue production semantics. |
| vn.py / VeighNa | Modular trading applications for gateways, CTA strategies, backtesting, paper account, data recording, risk manager, portfolio manager. | Practical module separation: gateway, strategy, paper account, data recorder, risk management. | China-market gateway breadth, GUI framework, full plugin ecosystem. |
| OpenAlgo | Unified broker API, WebSocket streaming, sandbox mode, REST API layer, broker switching, latency/PnL monitoring. | Unified adapter idea, sandbox-first safety stance, future FastAPI/API layer, latency metrics as a later phase. | Full web platform, React UI, many broker integrations, visual strategy builder. |
| quanttrader | Python backtest/live trading orientation and strategy execution examples. | Lightweight Python project style and simple extensibility. | Treating the project mainly as strategy/backtest framework instead of OMS infrastructure. |
| InteractiveBrokers-Algo-Trading-API | IB price feeds, order tracking, margin tracking, execution handling, retry counters, kill switches, paper/live gateway separation. | Order tracking, kill switch, explicit adapter boundary, separation between market data and order execution processes. | Direct IB/TWS dependency, MySQL-first persistence, live connectivity in early phases. |
| Event-driven backtesting examples | MarketEvent -> SignalEvent -> OrderEvent -> FillEvent -> Portfolio update, FIFO/chronological event processing, avoidance of lookahead bias. | MVP trading flow: market data event -> strategy signal -> risk check -> order -> broker -> fill -> portfolio/PnL update. | Full historical research engine, slippage/commission models, advanced scheduling. |

## Key Lessons

### 1. Event-driven flow is the right mental model

Trading systems react to things that happen: market data arrives, a strategy emits a signal, an order is submitted, a fill is reported, and the account changes. Even if the MVP uses a simple CLI loop, its modules should look like event handlers. This keeps the project close to production trading architecture without requiring a production event bus on day one.

### 2. Broker adapters protect the core

The core OMS should not know whether execution comes from MockBroker, Alpaca Paper, IBKR, or FIX. A `BrokerAdapter` boundary lets tests use deterministic execution while future integrations translate external broker APIs into the same internal order/fill model.

### 3. OMS and portfolio are separate responsibilities

The OMS owns order identity, status transitions, and execution reports. Portfolio/account logic owns positions, cash, realized PnL, unrealized PnL, and equity. Merging them would make the system look like a strategy script. Separating them makes it look like trading infrastructure.

### 4. Pre-trade risk belongs before execution

The risk engine should reject unsafe orders before they reach the broker adapter. MVP rules should stay small: max order notional, cash check, max position, duplicate order guard, and kill switch.

### 5. Backtest/paper/live consistency is valuable, but MVP should start smaller

Mature systems try to make backtest and live execution share strategy code. This project will borrow that idea by keeping strategies independent from execution adapters. It will not implement a full backtesting engine in MVP because the resume target is OMS/execution infrastructure, not strategy research.

## Why Build A Smaller Mini OMS From Scratch

Using Lean, NautilusTrader, vn.py, or OpenAlgo directly would demonstrate tool usage, but it would hide the engineering decisions this resume project needs to show. A smaller from-scratch Mini OMS lets the project expose the important fundamentals:

- typed order and fill models
- explicit order lifecycle state machine
- pre-trade risk checks
- mock broker execution reports
- position/cash/PnL updates
- deterministic tests
- clean adapter boundaries for future broker and market data integrations

The MVP should stay intentionally modest. It should be small enough to understand in one sitting, but structured enough that a reviewer can see how it would grow into Alpaca Paper, FastAPI queries, SQLite persistence, Redis/Kafka event transport, ClickHouse market data storage, or a C++ performance module.

