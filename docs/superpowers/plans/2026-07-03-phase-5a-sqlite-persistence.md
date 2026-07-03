# Phase 5A SQLite Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a lightweight SQLite run-history store for deterministic trading runs.

**Architecture:** `TradingEngine` still returns an in-memory `TradingRunSummary`. A new `SQLiteRunStore` receives that summary after the run finishes and stores audit rows in SQLite. Core trading modules do not import persistence code.

**Tech Stack:** Python 3.12, standard-library `sqlite3`, `Decimal` values serialized as text, pytest, deterministic CLI demo.

---

## File Structure

- Create: `src/mini_trading/persistence/__init__.py`
  - Export persistence package symbols.
- Create: `src/mini_trading/persistence/sqlite.py`
  - Own SQLite schema creation, serialization helpers, `SQLiteRunStore.save_run()`, `list_runs()`, and `load_run()`.
- Create: `tests/unit/test_sqlite_run_store.py`
  - Unit tests for schema, saved rows, decimal serialization, duplicate IDs, and blank IDs.
- Modify: `src/mini_trading/app/cli_demo.py`
  - Add optional `--sqlite PATH` argument while preserving existing positional report-directory behavior.
- Modify: `tests/integration/test_cli_demo.py`
  - Add CLI/persistence integration tests.
- Modify: `README.md`
  - Document SQLite demo command.
- Modify: `docs/architecture.md`
  - Document persistence boundary and schema purpose.
- Modify: `docs/resume-and-interview-notes.md`
  - Add English Phase 5A interview notes.
- Modify: `docs/resume-and-interview-notes.zh.md`
  - Add Chinese Phase 5A interview notes.

---

### Task 1: SQLite Store Tests

**Files:**
- Create: `tests/unit/test_sqlite_run_store.py`

- [ ] **Step 1: Write failing unit tests**

```python
import sqlite3

import pytest

from mini_trading.app.cli_demo import run_demo
from mini_trading.persistence.sqlite import SQLiteRunStore


def test_initialize_schema_creates_expected_tables(tmp_path):
    db_path = tmp_path / "runs.sqlite"
    store = SQLiteRunStore(db_path)

    store.initialize_schema()

    with sqlite3.connect(db_path) as connection:
        table_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }

    assert {
        "runs",
        "signals",
        "orders",
        "fills",
        "account_snapshots",
        "snapshot_positions",
    }.issubset(table_names)


def test_save_run_persists_summary_counts_and_final_account(tmp_path):
    store = SQLiteRunStore(tmp_path / "runs.sqlite")

    store.save_run(run_id="demo-run", summary=run_demo())

    loaded = store.load_run("demo-run")

    assert loaded["run"]["run_id"] == "demo-run"
    assert loaded["run"]["events_processed"] == 4
    assert loaded["run"]["signal_count"] == 2
    assert loaded["run"]["order_count"] == 2
    assert loaded["run"]["fill_count"] == 2
    assert loaded["run"]["snapshot_count"] == 4
    assert loaded["run"]["final_cash"] == "100120"
    assert loaded["run"]["final_equity"] == "100120"
    assert loaded["run"]["realized_pnl"] == "120"
    assert loaded["run"]["unrealized_pnl"] == "0"


def test_save_run_persists_orders_fills_snapshots_and_positions(tmp_path):
    store = SQLiteRunStore(tmp_path / "runs.sqlite")

    store.save_run(run_id="demo-run", summary=run_demo())
    loaded = store.load_run("demo-run")

    assert loaded["signals"][0]["symbol"] == "AAPL"
    assert loaded["signals"][0]["side"] == "buy"
    assert loaded["signals"][0]["reference_price"] == "99"
    assert loaded["orders"][0]["order_id"] == "ord-1"
    assert loaded["orders"][0]["status"] == "filled"
    assert loaded["orders"][0]["filled_quantity"] == "10"
    assert loaded["fills"][0]["fill_id"] == "ord-1-fill-1"
    assert loaded["fills"][0]["notional"] == "990"
    assert loaded["account_snapshots"][2]["equity"] == "100070"
    assert loaded["snapshot_positions"][0]["symbol"] == "AAPL"
    assert loaded["snapshot_positions"][0]["quantity"] == "10"
    assert loaded["snapshot_positions"][0]["average_cost"] == "99"
    assert loaded["snapshot_positions"][0]["last_price"] == "106"


def test_list_runs_returns_saved_runs_in_created_order(tmp_path):
    store = SQLiteRunStore(tmp_path / "runs.sqlite")
    summary = run_demo()

    store.save_run(run_id="run-1", summary=summary)
    store.save_run(run_id="run-2", summary=summary)

    assert [row["run_id"] for row in store.list_runs()] == ["run-1", "run-2"]


def test_save_run_rejects_blank_run_id(tmp_path):
    store = SQLiteRunStore(tmp_path / "runs.sqlite")

    with pytest.raises(ValueError, match="run_id must not be blank"):
        store.save_run(run_id=" ", summary=run_demo())


def test_save_run_rejects_duplicate_run_id(tmp_path):
    store = SQLiteRunStore(tmp_path / "runs.sqlite")
    summary = run_demo()

    store.save_run(run_id="demo-run", summary=summary)

    with pytest.raises(sqlite3.IntegrityError):
        store.save_run(run_id="demo-run", summary=summary)
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_sqlite_run_store.py -q
```

Expected: FAIL because `mini_trading.persistence.sqlite` does not exist.

---

### Task 2: SQLite Store Implementation

**Files:**
- Create: `src/mini_trading/persistence/__init__.py`
- Create: `src/mini_trading/persistence/sqlite.py`

- [ ] **Step 1: Implement minimal store**

Create `SQLiteRunStore` with:

- schema DDL for six tables
- `initialize_schema()`
- `save_run()`
- `list_runs()`
- `load_run()`
- helper functions for `Decimal`, `datetime`, and row dictionaries

Key requirements:

- use `sqlite3.connect()`
- set `connection.row_factory = sqlite3.Row`
- execute `PRAGMA foreign_keys = ON`
- call `initialize_schema()` inside read/write methods
- store decimals using `str(value)`
- store datetimes using `value.isoformat()`
- save a run inside one transaction

- [ ] **Step 2: Run unit tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\test_sqlite_run_store.py -q
```

Expected: PASS.

- [ ] **Step 3: Run full tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all existing and new tests pass.

---

### Task 3: CLI SQLite Output

**Files:**
- Modify: `src/mini_trading/app/cli_demo.py`
- Modify: `tests/integration/test_cli_demo.py`

- [ ] **Step 1: Write failing CLI tests**

Add tests:

```python
import sqlite3

from mini_trading.app.cli_demo import main, write_demo_sqlite


def test_write_demo_sqlite_creates_database(tmp_path):
    db_path = tmp_path / "demo.sqlite"

    written = write_demo_sqlite(db_path)

    assert written == db_path
    with sqlite3.connect(db_path) as connection:
        row = connection.execute(
            "SELECT run_id, events_processed, final_equity FROM runs"
        ).fetchone()
    assert row == ("demo", 4, "100120")


def test_cli_demo_can_write_sqlite_database(tmp_path, capsys):
    db_path = tmp_path / "demo.sqlite"

    main(["--sqlite", str(db_path)])

    output = capsys.readouterr().out
    assert "wrote_sqlite=" in output
    assert db_path.exists()
```

- [ ] **Step 2: Run tests to verify they fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\integration\test_cli_demo.py -q
```

Expected: FAIL because `write_demo_sqlite` and `--sqlite` do not exist.

- [ ] **Step 3: Implement CLI support**

Implementation shape:

```python
def write_demo_sqlite(db_path: str | Path, run_id: str = "demo") -> Path:
    summary = run_demo()
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    SQLiteRunStore(path).save_run(run_id=run_id, summary=summary)
    return path
```

Use `argparse` in `main()`:

- optional positional `output_dir`
- optional `--sqlite SQLITE_PATH`
- preserve summary printing
- preserve existing report directory output
- print `wrote_sqlite=<path>` when SQLite is written

- [ ] **Step 4: Run CLI tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\integration\test_cli_demo.py -q
```

Expected: PASS.

---

### Task 4: Documentation Updates

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/resume-and-interview-notes.md`
- Modify: `docs/resume-and-interview-notes.zh.md`

- [ ] **Step 1: Update docs**

Add:

- SQLite command example
- persistence boundary explanation
- Phase 5A progress notes
- interview framing for audit trail, transactions, SQLite, and Decimal-as-text

- [ ] **Step 2: Run tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: PASS.

---

### Task 5: Final Verification And Commit

**Files:**
- All Phase 5A files.

- [ ] **Step 1: Run full verification**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mini_trading.app.cli_demo --sqlite reports\demo.sqlite
```

Expected:

- pytest passes
- CLI prints deterministic summary
- CLI prints `wrote_sqlite=reports\demo.sqlite`

- [ ] **Step 2: Check git diff**

Run:

```powershell
git status --short
git diff --stat
```

Expected: only Phase 5A source, tests, and docs changed.

- [ ] **Step 3: Commit**

Run:

```powershell
git add src tests docs README.md
git commit -m "feat: add sqlite run persistence"
```
