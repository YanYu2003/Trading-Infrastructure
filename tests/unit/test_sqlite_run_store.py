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
    assert loaded["snapshot_positions"][0]["snapshot_index"] == 1
    assert loaded["snapshot_positions"][0]["last_price"] == "99"
    assert loaded["snapshot_positions"][1]["snapshot_index"] == 2
    assert loaded["snapshot_positions"][1]["last_price"] == "106"


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
