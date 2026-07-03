import json
from decimal import Decimal

from mini_trading.app.cli_demo import run_demo
from mini_trading.reports.replay import ReplayReport


def test_replay_report_converts_summary_to_dict():
    report = ReplayReport.from_summary(run_demo())

    data = report.to_dict()

    assert data["summary"]["events_processed"] == 4
    assert data["summary"]["signals"] == 2
    assert data["summary"]["orders"] == 2
    assert data["summary"]["fills"] == 2
    assert data["summary"]["final_equity"] == "100120"
    assert data["orders"][0]["status"] == "filled"
    assert data["fills"][0]["notional"] == "990"
    assert data["account_snapshots"][-1]["equity"] == "100120"


def test_replay_report_outputs_json():
    report = ReplayReport.from_summary(run_demo())

    payload = json.loads(report.to_json())

    assert payload["summary"]["final_cash"] == "100120"
    assert payload["summary"]["realized_pnl"] == "120"


def test_replay_report_outputs_orders_csv():
    report = ReplayReport.from_summary(run_demo())

    csv_text = report.orders_csv()

    assert "order_id,symbol,side,order_type,quantity,filled_quantity,status" in csv_text
    assert "ord-1,AAPL,buy,market,10,10,filled" in csv_text


def test_replay_report_outputs_fills_csv():
    report = ReplayReport.from_summary(run_demo())

    csv_text = report.fills_csv()

    assert "fill_id,order_id,symbol,side,price,quantity,notional" in csv_text
    assert "ord-1-fill-1,ord-1,AAPL,buy,99,10,990" in csv_text


def test_replay_report_outputs_account_snapshots_csv():
    report = ReplayReport.from_summary(run_demo())

    csv_text = report.account_snapshots_csv()

    assert "index,cash,gross_market_value,equity,realized_pnl,unrealized_pnl" in csv_text
    assert "3,100120,0,100120,120,0" in csv_text

