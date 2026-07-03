# Phase 2 Mini OMS Risk Broker Portfolio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic local trading core that connects pre-trade risk, order management, mock execution, and portfolio/PnL updates.

**Architecture:** Phase 2 keeps responsibilities separate. `RiskEngine` validates orders before execution, `MockBroker` converts accepted orders into deterministic fills or rejects, `Portfolio` applies fills to cash/positions/PnL, and `OrderManager` orchestrates the flow while preserving the Phase 1 order state machine.

**Tech Stack:** Python dataclasses, `decimal.Decimal`, pytest, standard-library protocols/ABCs.

---

### Task 1: Risk Engine

**Files:**
- Create: `src/mini_trading/core/risk.py`
- Test: `tests/unit/test_risk.py`

- [ ] **Step 1: Write failing tests**

Add tests for allowed orders, kill switch rejection, max notional rejection, cash rejection, max position rejection, sell quantity rejection, and duplicate open order rejection.

- [ ] **Step 2: Run risk tests and verify failure**

Run: `python -m pytest tests/unit/test_risk.py -q`

Expected: failure because `mini_trading.core.risk` does not exist.

- [ ] **Step 3: Implement minimal RiskEngine**

Create `RiskLimits`, `RiskCheckResult`, and `RiskEngine.check_order(order, account, reference_price, open_orders=())`.

- [ ] **Step 4: Run risk tests and verify pass**

Run: `python -m pytest tests/unit/test_risk.py -q`

Expected: all risk tests pass.

### Task 2: Portfolio

**Files:**
- Create: `src/mini_trading/core/portfolio.py`
- Test: `tests/unit/test_portfolio.py`

- [ ] **Step 1: Write failing tests**

Add tests for buy fill cash/position updates, weighted average cost, sell fill realized PnL, rejecting oversell, mark-to-market, and account snapshot.

- [ ] **Step 2: Run portfolio tests and verify failure**

Run: `python -m pytest tests/unit/test_portfolio.py -q`

Expected: failure because `mini_trading.core.portfolio` does not exist.

- [ ] **Step 3: Implement minimal Portfolio**

Create immutable `Portfolio` with `apply_fill(fill)`, `mark_price(symbol, price)`, and `snapshot()`.

- [ ] **Step 4: Run portfolio tests and verify pass**

Run: `python -m pytest tests/unit/test_portfolio.py -q`

Expected: all portfolio tests pass.

### Task 3: Broker Adapter And MockBroker

**Files:**
- Create: `src/mini_trading/brokers/base.py`
- Create: `src/mini_trading/brokers/mock.py`
- Test: `tests/unit/test_mock_broker.py`

- [ ] **Step 1: Write failing tests**

Add tests for market order full fill, limit buy not filled when price is above limit, limit buy fill when price is at/below limit, partial fill mode, and broker reject mode.

- [ ] **Step 2: Run broker tests and verify failure**

Run: `python -m pytest tests/unit/test_mock_broker.py -q`

Expected: failure because broker modules do not exist.

- [ ] **Step 3: Implement minimal broker modules**

Create `BrokerResult`, `BrokerAdapter` protocol, and `MockBroker.submit_order(order, market_price)`.

- [ ] **Step 4: Run broker tests and verify pass**

Run: `python -m pytest tests/unit/test_mock_broker.py -q`

Expected: all broker tests pass.

### Task 4: OrderManager

**Files:**
- Create: `src/mini_trading/core/oms.py`
- Test: `tests/unit/test_oms.py`
- Test: `tests/integration/test_order_execution_flow.py`

- [ ] **Step 1: Write failing tests**

Add tests for risk rejection, market order full fill, partial fill status, broker rejection, and end-to-end order/portfolio updates.

- [ ] **Step 2: Run OMS tests and verify failure**

Run: `python -m pytest tests/unit/test_oms.py tests/integration/test_order_execution_flow.py -q`

Expected: failure because `mini_trading.core.oms` does not exist.

- [ ] **Step 3: Implement minimal OrderManager**

Create `OrderManager` that creates immutable orders, calls risk, submits to broker, applies fills to portfolio, and stores order history.

- [ ] **Step 4: Run OMS and integration tests and verify pass**

Run: `python -m pytest tests/unit/test_oms.py tests/integration/test_order_execution_flow.py -q`

Expected: all OMS tests pass.

### Task 5: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/resume-and-interview-notes.md`
- Modify: `docs/resume-and-interview-notes.zh.md`

- [ ] **Step 1: Update documentation**

Record Phase 2 completed behavior, new key interview concepts, and upgraded resume bullets in both English and Chinese notes.

- [ ] **Step 2: Run full verification**

Run: `python -m pytest -q`

Expected: all tests pass.

- [ ] **Step 3: Confirm local Python version**

Run: `python --version`

Expected: report actual local version in final notes if it remains below target Python 3.11.

