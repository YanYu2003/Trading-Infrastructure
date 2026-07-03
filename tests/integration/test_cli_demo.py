import sqlite3
from decimal import Decimal

from mini_trading.app.cli_demo import main, run_demo, write_demo_reports, write_demo_sqlite


def test_run_demo_returns_deterministic_trading_summary():
    summary = run_demo()

    assert summary.events_processed == 4
    assert len(summary.signals) == 2
    assert len(summary.order_results) == 2
    assert len(summary.fills) == 2
    assert summary.account.cash == Decimal("100120")
    assert summary.account.equity == Decimal("100120")


def test_write_demo_reports_creates_json_and_csv_files(tmp_path):
    written = write_demo_reports(tmp_path)

    assert set(path.name for path in written) == {
        "summary.json",
        "orders.csv",
        "fills.csv",
        "account_snapshots.csv",
    }
    assert (tmp_path / "summary.json").read_text(encoding="utf-8").startswith("{")
    assert "ord-1,AAPL,buy,market,10,10,filled" in (
        tmp_path / "orders.csv"
    ).read_text(encoding="utf-8")
    assert "ord-1-fill-1,ord-1,AAPL,buy,99,10,990" in (
        tmp_path / "fills.csv"
    ).read_text(encoding="utf-8")
    assert "3,100120,0,100120,120,0" in (
        tmp_path / "account_snapshots.csv"
    ).read_text(encoding="utf-8")


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
