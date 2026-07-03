# Phase 5A SQLite Persistence Design

## Goal

Add a lightweight SQLite persistence layer for deterministic trading runs. The system should save run summaries, strategy signals, orders, fills, account snapshots, and per-snapshot positions so a demo run can be audited after the process exits.

## Context

The current project keeps trading state in memory and can export replay artifacts as JSON and CSV through `ReplayReport`. That is enough for a basic demo, but it is not queryable and does not represent a durable run history.

Phase 5A adds a database boundary without changing the core trading flow:

```text
TradingEngine -> TradingRunSummary -> SQLiteRunStore -> SQLite database
```

The persistence layer receives completed run summaries. It does not submit orders, apply risk checks, execute fills, mutate portfolio state, or drive strategy behavior.

## Recommended Approach

Use Python's standard-library `sqlite3` module behind a small repository-style adapter:

- create `mini_trading.persistence.sqlite.SQLiteRunStore`
- keep all schema creation and SQL statements inside the persistence package
- store exact financial decimals as text, not floating-point numbers
- store datetimes as ISO-8601 text
- wrap each saved run in one transaction
- keep core modules independent from SQLite

This keeps the feature small, deterministic, and easy to explain in interviews.

## Module Boundaries

### New Package

`src/mini_trading/persistence/`

Responsibilities:

- create and initialize SQLite schema
- save one `TradingRunSummary` under a `run_id`
- load persisted run history as read-model rows
- expose simple query methods for tests, CLI, and future read-only APIs

### Existing Core Modules

`src/mini_trading/core/*`

Responsibilities remain unchanged:

- market data event processing
- strategy signal generation
- risk checks
- order lifecycle
- mock execution
- portfolio and PnL calculation

Core modules must not import `mini_trading.persistence`.

### CLI Demo

`src/mini_trading/app/cli_demo.py`

Add an optional SQLite output path:

```powershell
python -m mini_trading.app.cli_demo --sqlite reports/demo.sqlite
```

The existing JSON/CSV output directory behavior must keep working:

```powershell
python -m mini_trading.app.cli_demo reports/demo
```

If both are provided, the demo writes both artifact types.

## Schema

The schema is intentionally normalized enough for audit queries while staying small.

### `runs`

One row per completed engine run.

Columns:

- `run_id TEXT PRIMARY KEY`
- `created_at TEXT NOT NULL`
- `events_processed INTEGER NOT NULL`
- `signal_count INTEGER NOT NULL`
- `order_count INTEGER NOT NULL`
- `fill_count INTEGER NOT NULL`
- `snapshot_count INTEGER NOT NULL`
- `final_cash TEXT NOT NULL`
- `final_gross_market_value TEXT NOT NULL`
- `final_equity TEXT NOT NULL`
- `realized_pnl TEXT NOT NULL`
- `unrealized_pnl TEXT NOT NULL`

### `signals`

One row per strategy signal in run order.

Columns:

- `run_id TEXT NOT NULL`
- `signal_index INTEGER NOT NULL`
- `symbol TEXT NOT NULL`
- `side TEXT NOT NULL`
- `order_type TEXT NOT NULL`
- `quantity TEXT NOT NULL`
- `reference_price TEXT NOT NULL`
- primary key: `(run_id, signal_index)`
- foreign key: `run_id -> runs.run_id`

### `orders`

One row per final order result.

Columns:

- `run_id TEXT NOT NULL`
- `order_id TEXT NOT NULL`
- `symbol TEXT NOT NULL`
- `side TEXT NOT NULL`
- `order_type TEXT NOT NULL`
- `quantity TEXT NOT NULL`
- `limit_price TEXT`
- `filled_quantity TEXT NOT NULL`
- `status TEXT NOT NULL`
- `created_at TEXT`
- primary key: `(run_id, order_id)`
- foreign key: `run_id -> runs.run_id`

### `fills`

One row per execution fill.

Columns:

- `run_id TEXT NOT NULL`
- `fill_id TEXT NOT NULL`
- `order_id TEXT NOT NULL`
- `symbol TEXT NOT NULL`
- `side TEXT NOT NULL`
- `price TEXT NOT NULL`
- `quantity TEXT NOT NULL`
- `notional TEXT NOT NULL`
- `timestamp TEXT NOT NULL`
- primary key: `(run_id, fill_id)`
- foreign key: `run_id -> runs.run_id`

### `account_snapshots`

One row per account state recorded by the engine.

Columns:

- `run_id TEXT NOT NULL`
- `snapshot_index INTEGER NOT NULL`
- `cash TEXT NOT NULL`
- `gross_market_value TEXT NOT NULL`
- `equity TEXT NOT NULL`
- `realized_pnl TEXT NOT NULL`
- `unrealized_pnl TEXT NOT NULL`
- primary key: `(run_id, snapshot_index)`
- foreign key: `run_id -> runs.run_id`

### `snapshot_positions`

One row per position inside each account snapshot.

Columns:

- `run_id TEXT NOT NULL`
- `snapshot_index INTEGER NOT NULL`
- `symbol TEXT NOT NULL`
- `quantity TEXT NOT NULL`
- `average_cost TEXT NOT NULL`
- `last_price TEXT NOT NULL`
- `market_value TEXT NOT NULL`
- `unrealized_pnl TEXT NOT NULL`
- primary key: `(run_id, snapshot_index, symbol)`
- foreign key: `(run_id, snapshot_index) -> account_snapshots(run_id, snapshot_index)`

## Data Representation

Financial values use `Decimal` in the domain model. SQLite does not have a native decimal type, and storing these values as `REAL` would introduce floating-point rounding risk. Phase 5A stores decimals as exact text with `str(decimal_value)`.

Datetimes are stored as ISO-8601 strings. Values that are absent in the domain model, such as `Order.created_at` for some tests, are stored as `NULL`.

Enum values use their existing `.value` strings so persisted rows match CSV/JSON report terminology.

## API Design

Create `SQLiteRunStore` with these methods:

```python
class SQLiteRunStore:
    def __init__(self, db_path: str | Path) -> None: ...

    def initialize_schema(self) -> None: ...

    def save_run(
        self,
        *,
        run_id: str,
        summary: TradingRunSummary,
        created_at: datetime | None = None,
    ) -> None: ...

    def list_runs(self) -> list[dict[str, str | int]]: ...

    def load_run(self, run_id: str) -> dict[str, object]: ...
```

`save_run()` rejects blank run IDs. Duplicate run IDs are not overwritten; SQLite primary key enforcement should surface that mistake during tests and demos.

`load_run()` returns a read-model dictionary with these keys:

- `run`
- `signals`
- `orders`
- `fills`
- `account_snapshots`
- `snapshot_positions`

This API is deliberately read-model oriented. It is not responsible for reconstructing a live `TradingEngine`, `Portfolio`, or `OrderManager`.

## Transaction And Integrity Rules

- `initialize_schema()` is idempotent.
- `save_run()` uses one database transaction.
- Foreign keys are enabled with `PRAGMA foreign_keys = ON`.
- A run is saved completely or not saved at all.
- Duplicate primary keys fail instead of silently replacing historical data.

## Testing Plan

Use TDD and standard-library temporary directories.

Unit tests:

- schema initialization creates all expected tables
- saving a demo summary persists run counts and final account values
- saved orders preserve status, side, type, quantity, filled quantity, and optional limit price
- saved fills preserve price, quantity, notional, timestamp, and linked order ID
- account snapshots and per-snapshot positions are persisted
- decimals are stored as exact strings rather than floats
- duplicate `run_id` saves fail
- blank `run_id` saves fail with `ValueError`

Integration tests:

- CLI demo can write a SQLite database
- existing CLI summary output still works
- existing JSON/CSV report output still works

## Documentation Updates

After implementation:

- update `README.md` with the SQLite demo command
- update `docs/architecture.md` with the persistence boundary
- update `docs/resume-and-interview-notes.md`
- update `docs/resume-and-interview-notes.zh.md`

## Out Of Scope

Phase 5A does not add:

- live trading
- paper broker connectivity
- async database access
- SQLAlchemy or another ORM
- market data tick persistence
- schema migrations beyond idempotent MVP table creation
- reconstructing a running portfolio object from database rows
- performance claims or strategy profitability claims

## Interview Framing

This phase demonstrates that the project can separate trading state transitions from persistence. The core system computes facts in memory; the persistence adapter records those facts durably and transactionally. In an interview, this can be described as a clean architecture boundary plus an audit-trail feature.

Key talking points:

- SQLite is chosen because the MVP needs local durability and queryability, not a distributed database.
- Decimal values are stored as text to avoid financial rounding errors.
- The database adapter depends on the domain summary, but the domain does not depend on the database.
- A transaction protects run integrity: partial run history is not acceptable for an audit record.
- Position snapshots make PnL explainable, not just visible as account-level totals.
