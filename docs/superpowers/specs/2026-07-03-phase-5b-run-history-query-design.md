# Phase 5B Run History Query Design

## Goal

Add a read-only run-history query layer for SQLite persistence. A user should be able to inspect saved trading runs, orders, fills, account snapshots, and per-snapshot positions from the command line without touching the trading core.

## Context

Phase 5A added `SQLiteRunStore`, which can save a completed `TradingRunSummary` into SQLite and load the persisted read model as dictionaries.

Phase 5B builds on that persistence boundary:

```text
SQLite database -> SQLiteRunStore -> run_history CLI -> human-readable audit output
```

This phase is about audit and inspection. It does not submit orders, run strategies, mutate portfolio state, or reconstruct a live trading engine.

## User-Facing Commands

Create a new CLI module:

```powershell
python -m mini_trading.app.run_history <database> <command> [args]
```

Supported commands:

```powershell
python -m mini_trading.app.run_history reports/demo.sqlite list-runs
python -m mini_trading.app.run_history reports/demo.sqlite show-run demo
python -m mini_trading.app.run_history reports/demo.sqlite orders demo
python -m mini_trading.app.run_history reports/demo.sqlite fills demo
python -m mini_trading.app.run_history reports/demo.sqlite snapshots demo
python -m mini_trading.app.run_history reports/demo.sqlite positions demo
python -m mini_trading.app.run_history reports/demo.sqlite positions demo --snapshot-index 2
```

The CLI output should be compact CSV-style text with a header row. This keeps it deterministic, easy to test, and easy to copy into spreadsheets or terminal notes.

## Design

### New Module

`src/mini_trading/app/run_history.py`

Responsibilities:

- parse command-line arguments
- call `SQLiteRunStore`
- select the requested read-model rows
- print stable CSV-style text to stdout
- return non-zero process exit on missing run IDs through normal Python exceptions

### Existing Store

`src/mini_trading/persistence/sqlite.py`

No schema changes are required. The existing `list_runs()` and `load_run()` methods are enough for Phase 5B.

If implementation reveals repeated row filtering logic, add small helper functions in `run_history.py` rather than expanding persistence responsibilities.

### Output Shape

`list-runs` prints:

```text
run_id,events_processed,signal_count,order_count,fill_count,snapshot_count,final_equity,realized_pnl,unrealized_pnl
demo,4,2,2,2,4,100120,120,0
```

`show-run demo` prints one run summary row:

```text
run_id,created_at,events_processed,signal_count,order_count,fill_count,snapshot_count,final_cash,final_gross_market_value,final_equity,realized_pnl,unrealized_pnl
demo,...
```

`orders demo` prints:

```text
order_id,symbol,side,order_type,quantity,limit_price,filled_quantity,status,created_at
ord-1,AAPL,buy,market,10,,10,filled,
```

`fills demo` prints:

```text
fill_id,order_id,symbol,side,price,quantity,notional,timestamp
ord-1-fill-1,ord-1,AAPL,buy,99,10,990,...
```

`snapshots demo` prints:

```text
snapshot_index,cash,gross_market_value,equity,realized_pnl,unrealized_pnl
0,100000,0,100000,0,0
```

`positions demo` prints:

```text
snapshot_index,symbol,quantity,average_cost,last_price,market_value,unrealized_pnl
1,AAPL,10,99,99,990,0
```

`positions demo --snapshot-index 2` filters positions to one account snapshot.

## Error Handling

Keep Phase 5B simple:

- missing database files are allowed to create an empty schema through the existing store behavior
- missing run IDs raise `KeyError`
- invalid subcommands are handled by `argparse`
- missing required `run_id` arguments are handled by `argparse`

This keeps the CLI small and deterministic. Friendly error wrapping can be added later if the CLI becomes a primary user interface.

## Testing Plan

Use deterministic demo data written through `write_demo_sqlite()`.

Integration tests should cover:

- `list-runs` output includes the demo run and final equity
- `show-run demo` output includes run counts and final PnL
- `orders demo` output includes both filled orders
- `fills demo` output includes both fills and notional values
- `snapshots demo` output includes mark-to-market equity changes
- `positions demo` output includes AAPL position rows
- `positions demo --snapshot-index 2` filters to the requested snapshot

Unit-level formatter tests are optional. If formatting logic stays small inside `run_history.py`, integration tests are enough.

## Documentation Updates

After implementation:

- update `README.md` with run-history query examples
- update `docs/architecture.md` with the read-only query boundary
- update `docs/resume-and-interview-notes.md`
- update `docs/resume-and-interview-notes.zh.md`

## Out Of Scope

Phase 5B does not add:

- FastAPI
- charts or dashboards
- ORM
- schema migrations
- market data tick storage
- order replay into a live engine
- editable database operations
- production-grade CLI UX

## Interview Framing

Phase 5B demonstrates that persistence is not just "dumping rows." The system can now save a trading run and inspect it through a read-only audit interface.

Key talking points:

- The query CLI depends on the persistence read model, not on the trading core.
- The output is deterministic and testable.
- The user can inspect orders, fills, account snapshots, and positions after the process exits.
- The design prepares the project for a future FastAPI read-only layer because the query semantics are already separated from OMS and portfolio logic.
