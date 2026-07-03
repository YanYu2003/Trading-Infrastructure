from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query

from mini_trading.persistence.sqlite import SQLiteRunStore


DEFAULT_DB_PATH = Path(os.getenv("MINI_TRADING_DB", "reports/demo.sqlite"))


def create_app(db_path: str | Path = DEFAULT_DB_PATH) -> FastAPI:
    store = SQLiteRunStore(db_path)
    app = FastAPI(
        title="Mini Trading Infrastructure Read API",
        version="0.1.0",
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "mode": "read-only"}

    @app.get("/runs")
    def list_runs() -> dict[str, list[dict[str, Any]]]:
        return {"runs": store.list_runs()}

    @app.get("/runs/{run_id}")
    def show_run(run_id: str) -> dict[str, dict[str, Any]]:
        loaded = _load_or_404(store, run_id)
        return {"run": loaded["run"]}

    @app.get("/runs/{run_id}/orders")
    def orders(run_id: str) -> dict[str, list[dict[str, Any]]]:
        loaded = _load_or_404(store, run_id)
        return {"orders": loaded["orders"]}

    @app.get("/runs/{run_id}/fills")
    def fills(run_id: str) -> dict[str, list[dict[str, Any]]]:
        loaded = _load_or_404(store, run_id)
        return {"fills": loaded["fills"]}

    @app.get("/runs/{run_id}/snapshots")
    def snapshots(run_id: str) -> dict[str, list[dict[str, Any]]]:
        loaded = _load_or_404(store, run_id)
        return {"account_snapshots": loaded["account_snapshots"]}

    @app.get("/runs/{run_id}/positions")
    def positions(
        run_id: str,
        snapshot_index: int | None = Query(default=None),
    ) -> dict[str, list[dict[str, Any]]]:
        loaded = _load_or_404(store, run_id)
        rows = list(loaded["snapshot_positions"])
        if snapshot_index is not None:
            rows = [
                row
                for row in rows
                if row["snapshot_index"] == snapshot_index
            ]
        return {"positions": rows}

    return app


def _load_or_404(store: SQLiteRunStore, run_id: str) -> dict[str, Any]:
    try:
        return store.load_run(run_id)
    except KeyError as error:
        raise HTTPException(
            status_code=404,
            detail=f"run_id not found: {run_id}",
        ) from error


app = create_app()
