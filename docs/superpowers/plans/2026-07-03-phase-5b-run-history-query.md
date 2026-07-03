# Phase 5B Run History Query Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a read-only CLI for inspecting persisted SQLite trading run history.

**Architecture:** Reuse `SQLiteRunStore` as the database boundary and add a thin CLI module that loads read-model dictionaries and prints deterministic CSV-style output. The trading core remains independent from persistence and query code.

**Tech Stack:** Python 3.12, standard-library `argparse`, `csv`, `io.StringIO`, SQLite through existing `SQLiteRunStore`, pytest integration tests.

---

## File Structure

- Create: `src/mini_trading/app/run_history.py`
  - Parse CLI commands and print read-only run-history tables.
- Create: `tests/integration/test_run_history_cli.py`
  - Integration tests using deterministic demo SQLite files.
- Modify: `README.md`
  - Add run-history query command examples.
- Modify: `docs/architecture.md`
  - Add Phase 5B query boundary.
- Modify: `docs/resume-and-interview-notes.md`
  - Add English Phase 5B notes.
- Modify: `docs/resume-and-interview-notes.zh.md`
  - Add Chinese Phase 5B notes.

---

### Task 1: Run History CLI Tests

**Files:**
- Create: `tests/integration/test_run_history_cli.py`

- [ ] **Step 1: Write failing integration tests**

```python
from mini_trading.app.cli_demo import write_demo_sqlite
from mini_trading.app.run_history import main


def _demo_db(tmp_path):
    db_path = tmp_path / "demo.sqlite"
    write_demo_sqlite(db_path)
    return db_path


def test_list_runs_outputs_saved_run(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "list-runs"])

    output = capsys.readouterr().out
    assert "run_id,events_processed,signal_count,order_count,fill_count,snapshot_count,final_equity,realized_pnl,unrealized_pnl" in output
    assert "demo,4,2,2,2,4,100120,120,0" in output


def test_show_run_outputs_single_run_summary(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "show-run", "demo"])

    output = capsys.readouterr().out
    assert "run_id,created_at,events_processed,signal_count,order_count,fill_count,snapshot_count,final_cash,final_gross_market_value,final_equity,realized_pnl,unrealized_pnl" in output
    assert "demo," in output
    assert ",4,2,2,2,4,100120,0,100120,120,0" in output


def test_orders_outputs_order_rows(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "orders", "demo"])

    output = capsys.readouterr().out
    assert "order_id,symbol,side,order_type,quantity,limit_price,filled_quantity,status,created_at" in output
    assert "ord-1,AAPL,buy,market,10,,10,filled," in output
    assert "ord-2,AAPL,sell,market,10,,10,filled," in output


def test_fills_outputs_fill_rows(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "fills", "demo"])

    output = capsys.readouterr().out
    assert "fill_id,order_id,symbol,side,price,quantity,notional,timestamp" in output
    assert "ord-1-fill-1,ord-1,AAPL,buy,99,10,990," in output
    assert "ord-2-fill-1,ord-2,AAPL,sell,111,10,1110," in output


def test_snapshots_outputs_account_snapshot_rows(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "snapshots", "demo"])

    output = capsys.readouterr().out
    assert "snapshot_index,cash,gross_market_value,equity,realized_pnl,unrealized_pnl" in output
    assert "0,100000,0,100000,0,0" in output
    assert "2,99010,1060,100070,0,70" in output
    assert "3,100120,0,100120,120,0" in output


def test_positions_outputs_position_rows(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "positions", "demo"])

    output = capsys.readouterr().out
    assert "snapshot_index,symbol,quantity,average_cost,last_price,market_value,unrealized_pnl" in output
    assert "1,AAPL,10,99,99,990,0" in output
    assert "2,AAPL,10,99,106,1060,70" in output


def test_positions_can_filter_by_snapshot_index(tmp_path, capsys):
    db_path = _demo_db(tmp_path)

    main([str(db_path), "positions", "demo", "--snapshot-index", "2"])

    output = capsys.readouterr().out
    assert "2,AAPL,10,99,106,1060,70" in output
    assert "1,AAPL,10,99,99,990,0" not in output
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\integration\test_run_history_cli.py -q
```

Expected: FAIL because `mini_trading.app.run_history` does not exist.

---

### Task 2: Run History CLI Implementation

**Files:**
- Create: `src/mini_trading/app/run_history.py`

- [ ] **Step 1: Implement CLI module**

Implementation requirements:

- define `main(argv: list[str] | None = None) -> None`
- use `argparse`
- create subcommands: `list-runs`, `show-run`, `orders`, `fills`, `snapshots`, `positions`
- `positions` accepts optional `--snapshot-index int`
- use `SQLiteRunStore`
- write rows through `csv.DictWriter` with `lineterminator="\n"`
- print output with `end=""` so tests do not get extra blank lines

Suggested helpers:

```python
def _csv_text(fieldnames: list[str], rows: list[dict]) -> str: ...
def _select_fields(rows: list[dict], fieldnames: list[str]) -> list[dict]: ...
def _print_rows(fieldnames: list[str], rows: list[dict]) -> None: ...
```

- [ ] **Step 2: Run CLI tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\integration\test_run_history_cli.py -q
```

Expected: PASS.

- [ ] **Step 3: Run full tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

Run:

```powershell
git add src\mini_trading\app\run_history.py tests\integration\test_run_history_cli.py
git commit -m "feat: add run history query cli"
```

---

### Task 3: Documentation Updates

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/resume-and-interview-notes.md`
- Modify: `docs/resume-and-interview-notes.zh.md`

- [ ] **Step 1: Update documentation**

Add:

- `python -m mini_trading.app.run_history` examples
- read-only query boundary explanation
- Phase 5B current status
- interview framing for audit query layer
- resume bullet upgrade

- [ ] **Step 2: Run full tests**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: PASS.

- [ ] **Step 3: Commit**

Run:

```powershell
git add README.md docs\architecture.md docs\resume-and-interview-notes.md docs\resume-and-interview-notes.zh.md
git commit -m "docs: document run history query phase"
```

---

### Task 4: Final Verification

**Files:**
- All Phase 5B files.

- [ ] **Step 1: Run full test suite**

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run manual CLI smoke test**

Run:

```powershell
$dbPath = Join-Path $env:TEMP "mini-trading-phase5b-demo.sqlite"
.\.venv\Scripts\python.exe -m mini_trading.app.cli_demo --sqlite $dbPath
.\.venv\Scripts\python.exe -m mini_trading.app.run_history $dbPath list-runs
.\.venv\Scripts\python.exe -m mini_trading.app.run_history $dbPath positions demo --snapshot-index 2
```

Expected:

- first command prints deterministic demo summary
- second command includes `demo,4,2,2,2,4,100120,120,0`
- third command includes `2,AAPL,10,99,106,1060,70`

- [ ] **Step 3: Check branch state**

Run:

```powershell
git status --short
git log --oneline master..HEAD
```

Expected:

- clean working tree
- Phase 5B commits listed
