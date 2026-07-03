# Phase 1 Core Models And Order State Machine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define the core trading data model and implement a tested order lifecycle state machine.

**Architecture:** Phase 1 creates small domain modules under `src/mini_trading/core`. Enums define shared vocabulary, dataclass models define typed trading entities, and `order_state.py` owns valid status transitions.

**Tech Stack:** Python dataclasses, `enum.Enum`, `decimal.Decimal`, pytest.

---

### Task 1: Core Enums And Models

**Files:**
- Create: `src/mini_trading/core/enums.py`
- Create: `src/mini_trading/core/models.py`
- Test: `tests/unit/test_core_models.py`

- [ ] **Step 1: Write failing model tests**

Add tests for symbol normalization, quote/trade construction, market order construction, limit order validation, fills, positions, and account snapshots.

- [ ] **Step 2: Run tests and verify they fail**

Run: `python -m pytest tests/unit/test_core_models.py -q`

Expected: failure because `mini_trading.core.enums` and `mini_trading.core.models` do not exist.

- [ ] **Step 3: Implement minimal enums and models**

Create enums for order side, order type, order status, and market data event type. Create dataclasses for `Symbol`, `Quote`, `Trade`, `MarketDataEvent`, `Order`, `Fill`, `Position`, `PnL`, and `AccountSnapshot`.

- [ ] **Step 4: Run tests and verify they pass**

Run: `python -m pytest tests/unit/test_core_models.py -q`

Expected: all model tests pass.

### Task 2: Order State Machine

**Files:**
- Create: `src/mini_trading/core/order_state.py`
- Test: `tests/unit/test_order_state.py`

- [ ] **Step 1: Write failing state machine tests**

Add tests for valid transitions, invalid transitions, terminal states, and applying transitions to an `Order`.

- [ ] **Step 2: Run tests and verify they fail**

Run: `python -m pytest tests/unit/test_order_state.py -q`

Expected: failure because `mini_trading.core.order_state` does not exist.

- [ ] **Step 3: Implement minimal state machine**

Create `VALID_ORDER_TRANSITIONS`, `InvalidOrderTransition`, `can_transition`, `assert_transition`, and `transition_order`.

- [ ] **Step 4: Run tests and verify they pass**

Run: `python -m pytest tests/unit/test_order_state.py -q`

Expected: all state machine tests pass.

### Task 3: Documentation And Full Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`

- [ ] **Step 1: Update docs**

Add a Phase 1 note describing the data model and order lifecycle.

- [ ] **Step 2: Run full tests**

Run: `python -m pytest -q`

Expected: all tests pass.

- [ ] **Step 3: Check Python version limitation**

Run: `python --version`

Expected: report the actual local version. If it is below 3.11, note that verification used the available interpreter and that the project target remains Python 3.11/3.12.

