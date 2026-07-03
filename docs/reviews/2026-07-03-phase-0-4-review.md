# Phase 0-4 Review

Date: 2026-07-03

## Scope

Reviewed the current mock-first Mini OMS project through Phase 4:

- core domain models and order state machine
- RiskEngine
- MockBroker
- Portfolio
- OrderManager
- MockMarketDataProvider
- PriceThresholdStrategy
- TradingEngine
- ReplayReport
- CLI demo
- README, architecture docs, and interview notes

## Verification Baseline

Before cleanup:

```text
python -m pytest -q
61 passed
```

The project is still not a git repository, and the local Python interpreter is still Python 3.10.10. The target project runtime remains Python 3.11 or 3.12.

## Findings

### Fixed: Strategy State Was Updated Before Execution Confirmation

`PriceThresholdStrategy` previously changed its internal position state when it emitted a signal. This made signal generation and execution confirmation too tightly coupled.

Why it mattered:

- A strategy signal is not an order.
- An order is not a fill.
- If a risk check or broker rejected the order, the strategy could still believe it had a position.
- That would block later valid buy signals and make strategy state diverge from portfolio state.

Fix:

- Added pending signal state to `PriceThresholdStrategy`.
- Added `on_order_result()` so the strategy updates confirmed position state only after execution feedback.
- Updated `TradingEngine` to call the strategy execution-feedback hook after `OrderManager.submit_order()`.
- Added a regression test proving rejected buy signals do not leave the strategy stuck.

### Residual Risk: Strategy State Is Still Simplified

The strategy currently tracks only a boolean `has_position`, not exact quantity. This is acceptable for the MVP threshold demo, but future multi-symbol or partial-fill strategy work should use actual portfolio state or a richer position view.

### Residual Risk: Partial Fills Are Single-Step In MVP

`MockBroker` can emit a deterministic partial fill, and `OrderManager` records `PARTIALLY_FILLED`. The project does not yet simulate later fills for the same open order. This is acceptable for current testing, but a future OMS phase should add incremental execution reports.

### Residual Risk: Persistence Is Missing

Orders, fills, and account snapshots are only in memory or exported as reports. SQLite persistence remains the recommended next feature before external broker integration.

### Residual Risk: Runtime Environment Needs Cleanup

The project target is Python 3.11/3.12, but the current machine only has Python 3.10.10 available through the Python launcher. A project-local `.venv` should be created after installing Python 3.11 or 3.12.

### Residual Risk: No Git Repository

The directory is still not a git repository. Before the next major phase, initialize git and commit the Phase 0-4 baseline.

## Review Result

The Phase 0-4 architecture remains aligned with the resume goal:

```text
MarketDataEvent
  -> StrategySignal
  -> RiskEngine
  -> OrderManager
  -> MockBroker
  -> Fill
  -> Portfolio
  -> ReplayReport
```

The codebase is ready for the next engineering phase after environment and git setup.

## Recommended Next Steps

1. Install Python 3.11 or 3.12.
2. Create a project-local `.venv`.
3. Initialize git and commit the current baseline.
4. Add SQLite persistence for orders, fills, and account snapshots.
5. Add a read-only query interface after persistence is stable.

