# Phase 0 Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the documented, safe, testable foundation for a Mini OMS trading infrastructure project.

**Architecture:** Phase 0 keeps trading logic out of scope and establishes clear boundaries for future work: domain core, broker adapters, market data providers, strategy modules, and thin application entry points. The first executable check is a smoke test proving the Python package can be imported and exposes safety defaults.

**Tech Stack:** Python 3.11 or 3.12, local `.venv`, pytest, src-layout Python package, Markdown docs.

---

### Task 1: Project Metadata And Safety Files

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `pyproject.toml`
- Create: `AGENTS.md`

- [ ] **Step 1: Add project metadata and ignored paths**

Create `.gitignore` with Python caches, build output, virtual environments, coverage output, logs, local env files, and editor state.

- [ ] **Step 2: Add environment example**

Create `.env.example` with `TRADING_MODE=mock`, `ENABLE_LIVE_TRADING=false`, and placeholder paper endpoint settings.

- [ ] **Step 3: Add Python project config**

Create `pyproject.toml` with package name `mini-trading-infra`, `requires-python = ">=3.11,<3.13"`, pytest configured to read from `tests`, and editable install support from `src`.

- [ ] **Step 4: Add agent rules**

Create `AGENTS.md` with the rules that all trading must default to mock or paper, live trading is disabled unless explicitly designed and reviewed in a future phase, secrets cannot be committed, and tests must pass before completion claims.

### Task 2: Research And Architecture Docs

**Files:**
- Create: `docs/research/open-source-comparison.md`
- Create: `docs/architecture.md`
- Create: `README.md`

- [ ] **Step 1: Write open-source comparison**

Summarize architecture lessons from QuantConnect Lean, NautilusTrader, vn.py, OpenAlgo, quanttrader, InteractiveBrokers-Algo-Trading-API, and event-driven backtesting examples. Focus on event-driven design, broker adapters, OMS/order tracking, pre-trade risk, market data, and backtest/live parity.

- [ ] **Step 2: Write project architecture**

Document the MVP architecture: MockMarketDataProvider, PriceThresholdStrategy, RiskEngine, OrderManager, MockBroker, Portfolio/Account/PnL, and CLI demo. Also document what the MVP intentionally excludes.

- [ ] **Step 3: Write README**

Document project purpose, safety stance, MVP scope, directory structure, phase roadmap, and setup commands using a local virtual environment.

### Task 3: Test-First Package Skeleton

**Files:**
- Create: `tests/unit/test_package_smoke.py`
- Create: `src/mini_trading/__init__.py`
- Create: `src/mini_trading/config.py`
- Create: `src/mini_trading/core/__init__.py`
- Create: `src/mini_trading/brokers/__init__.py`
- Create: `src/mini_trading/marketdata/__init__.py`
- Create: `src/mini_trading/strategies/__init__.py`
- Create: `src/mini_trading/app/__init__.py`

- [ ] **Step 1: Write the failing smoke test**

```python
from mini_trading import __version__
from mini_trading.config import DEFAULT_TRADING_MODE, LIVE_TRADING_ENABLED


def test_package_imports_with_safe_defaults():
    assert __version__ == "0.1.0"
    assert DEFAULT_TRADING_MODE == "mock"
    assert LIVE_TRADING_ENABLED is False
```

- [ ] **Step 2: Run the test and verify it fails**

Run: `python -m pytest tests/unit/test_package_smoke.py -q`

Expected: failure because `mini_trading` does not exist yet.

- [ ] **Step 3: Add the minimal package code**

Create the package modules with `__version__ = "0.1.0"` and safety defaults in `config.py`.

- [ ] **Step 4: Run the test and verify it passes**

Run: `python -m pytest tests/unit/test_package_smoke.py -q`

Expected: one passing test.

- [ ] **Step 5: Run the full test suite**

Run: `python -m pytest -q`

Expected: all tests pass.

