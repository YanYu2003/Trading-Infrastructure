# Phase 3 Event Driven Trading Flow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Connect deterministic mock market data, a price-threshold strategy, OrderManager, MockBroker, and Portfolio into a complete local event-driven trading loop.

**Architecture:** Phase 3 keeps I/O simulation at the edges. `MockMarketDataProvider` yields normalized `MarketDataEvent` objects, `PriceThresholdStrategy` converts trade events into `StrategySignal` objects, and `TradingEngine` routes signals into `OrderManager`. The engine remains synchronous and deterministic for MVP testing; future WebSocket/asyncio providers can implement the same market data boundary.

**Tech Stack:** Python dataclasses, iterables, `decimal.Decimal`, pytest, existing Phase 1/2 domain modules.

---

### Task 1: Mock Market Data Provider

**Files:**
- Create: `src/mini_trading/marketdata/base.py`
- Create: `src/mini_trading/marketdata/mock.py`
- Test: `tests/unit/test_mock_marketdata.py`

- [ ] **Step 1: Write failing tests**

Add tests showing deterministic trade event creation, quote event creation, event order preservation, and provider re-iterability.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/unit/test_mock_marketdata.py -q`

Expected: failure because market data modules do not exist.

- [ ] **Step 3: Implement minimal provider**

Create `MarketDataProvider` protocol and `MockMarketDataProvider` that yields normalized `MarketDataEvent` objects.

- [ ] **Step 4: Run tests and verify pass**

Run: `python -m pytest tests/unit/test_mock_marketdata.py -q`

Expected: all market data tests pass.

### Task 2: Price Threshold Strategy

**Files:**
- Create: `src/mini_trading/strategies/base.py`
- Create: `src/mini_trading/strategies/threshold.py`
- Test: `tests/unit/test_threshold_strategy.py`

- [ ] **Step 1: Write failing tests**

Add tests for buy signal below buy threshold, sell signal above sell threshold, no signal inside band, quote events ignored, and one-position state preventing duplicate buy signals.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/unit/test_threshold_strategy.py -q`

Expected: failure because strategy modules do not exist.

- [ ] **Step 3: Implement strategy and signal model**

Create `StrategySignal`, `Strategy` protocol, and `PriceThresholdStrategy.on_event(event)`.

- [ ] **Step 4: Run tests and verify pass**

Run: `python -m pytest tests/unit/test_threshold_strategy.py -q`

Expected: all strategy tests pass.

### Task 3: Trading Engine

**Files:**
- Create: `src/mini_trading/core/engine.py`
- Test: `tests/integration/test_event_driven_flow.py`

- [ ] **Step 1: Write failing integration tests**

Add tests that a deterministic market data stream triggers buy/sell orders, updates portfolio, records fills, and ignores quote-only streams.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/integration/test_event_driven_flow.py -q`

Expected: failure because `mini_trading.core.engine` does not exist.

- [ ] **Step 3: Implement minimal TradingEngine**

Create `TradingEngine.run()` that iterates market data events, asks the strategy for signals, submits orders through OrderManager, and returns a summary.

- [ ] **Step 4: Run tests and verify pass**

Run: `python -m pytest tests/integration/test_event_driven_flow.py -q`

Expected: all event-driven flow tests pass.

### Task 4: CLI Demo

**Files:**
- Create: `src/mini_trading/app/cli_demo.py`
- Test: `tests/integration/test_cli_demo.py`

- [ ] **Step 1: Write failing CLI test**

Add a test that `run_demo()` returns a summary with final account snapshot, orders, and fills.

- [ ] **Step 2: Run test and verify failure**

Run: `python -m pytest tests/integration/test_cli_demo.py -q`

Expected: failure because CLI demo module does not exist.

- [ ] **Step 3: Implement demo entry**

Create `run_demo()` and `main()` using deterministic AAPL events.

- [ ] **Step 4: Run test and verify pass**

Run: `python -m pytest tests/integration/test_cli_demo.py -q`

Expected: CLI demo test passes.

### Task 5: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/resume-and-interview-notes.md`
- Modify: `docs/resume-and-interview-notes.zh.md`

- [ ] **Step 1: Update docs**

Record Phase 3 completed behavior, event-driven concepts, strategy signal explanation, and upgraded resume bullets in English and Chinese notes.

- [ ] **Step 2: Run full verification**

Run: `python -m pytest -q`

Expected: all tests pass.

- [ ] **Step 3: Confirm local Python version**

Run: `python --version`

Expected: report the actual local version if it remains below target Python 3.11.

