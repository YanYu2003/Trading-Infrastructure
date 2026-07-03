from fastapi.testclient import TestClient

from mini_trading.app.api import create_app
from mini_trading.app.cli_demo import write_demo_sqlite


def _client(tmp_path) -> TestClient:
    db_path = tmp_path / "demo.sqlite"
    write_demo_sqlite(db_path)
    return TestClient(create_app(db_path))


def test_health_endpoint(tmp_path):
    client = _client(tmp_path)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mode": "read-only"}


def test_list_runs_endpoint(tmp_path):
    client = _client(tmp_path)

    response = client.get("/runs")

    assert response.status_code == 200
    assert response.json()["runs"][0]["run_id"] == "demo"
    assert response.json()["runs"][0]["final_equity"] == "100120"


def test_run_detail_endpoint(tmp_path):
    client = _client(tmp_path)

    response = client.get("/runs/demo")

    assert response.status_code == 200
    assert response.json()["run"]["events_processed"] == 4
    assert response.json()["run"]["realized_pnl"] == "120"


def test_orders_endpoint(tmp_path):
    client = _client(tmp_path)

    response = client.get("/runs/demo/orders")

    assert response.status_code == 200
    assert [row["order_id"] for row in response.json()["orders"]] == [
        "ord-1",
        "ord-2",
    ]


def test_fills_endpoint(tmp_path):
    client = _client(tmp_path)

    response = client.get("/runs/demo/fills")

    assert response.status_code == 200
    assert response.json()["fills"][0]["notional"] == "990"
    assert response.json()["fills"][1]["notional"] == "1110"


def test_snapshots_endpoint(tmp_path):
    client = _client(tmp_path)

    response = client.get("/runs/demo/snapshots")

    assert response.status_code == 200
    assert response.json()["account_snapshots"][2]["equity"] == "100070"


def test_positions_endpoint_can_filter_snapshot_index(tmp_path):
    client = _client(tmp_path)

    response = client.get("/runs/demo/positions", params={"snapshot_index": 2})

    assert response.status_code == 200
    assert response.json()["positions"] == [
        {
            "run_id": "demo",
            "snapshot_index": 2,
            "symbol": "AAPL",
            "quantity": "10",
            "average_cost": "99",
            "last_price": "106",
            "market_value": "1060",
            "unrealized_pnl": "70",
        }
    ]


def test_missing_run_returns_404(tmp_path):
    client = _client(tmp_path)

    response = client.get("/runs/missing")

    assert response.status_code == 404
    assert response.json() == {"detail": "run_id not found: missing"}
