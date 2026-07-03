from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from mini_trading.core.engine import TradingRunSummary
from mini_trading.core.models import AccountSnapshot, Fill, Order, Position
from mini_trading.core.oms import OrderSubmissionResult
from mini_trading.strategies.base import StrategySignal


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    events_processed INTEGER NOT NULL,
    signal_count INTEGER NOT NULL,
    order_count INTEGER NOT NULL,
    fill_count INTEGER NOT NULL,
    snapshot_count INTEGER NOT NULL,
    final_cash TEXT NOT NULL,
    final_gross_market_value TEXT NOT NULL,
    final_equity TEXT NOT NULL,
    realized_pnl TEXT NOT NULL,
    unrealized_pnl TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS signals (
    run_id TEXT NOT NULL,
    signal_index INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    order_type TEXT NOT NULL,
    quantity TEXT NOT NULL,
    reference_price TEXT NOT NULL,
    PRIMARY KEY (run_id, signal_index),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS orders (
    run_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    order_type TEXT NOT NULL,
    quantity TEXT NOT NULL,
    limit_price TEXT,
    filled_quantity TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT,
    PRIMARY KEY (run_id, order_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS fills (
    run_id TEXT NOT NULL,
    fill_id TEXT NOT NULL,
    order_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    price TEXT NOT NULL,
    quantity TEXT NOT NULL,
    notional TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    PRIMARY KEY (run_id, fill_id),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS account_snapshots (
    run_id TEXT NOT NULL,
    snapshot_index INTEGER NOT NULL,
    cash TEXT NOT NULL,
    gross_market_value TEXT NOT NULL,
    equity TEXT NOT NULL,
    realized_pnl TEXT NOT NULL,
    unrealized_pnl TEXT NOT NULL,
    PRIMARY KEY (run_id, snapshot_index),
    FOREIGN KEY (run_id) REFERENCES runs(run_id)
);

CREATE TABLE IF NOT EXISTS snapshot_positions (
    run_id TEXT NOT NULL,
    snapshot_index INTEGER NOT NULL,
    symbol TEXT NOT NULL,
    quantity TEXT NOT NULL,
    average_cost TEXT NOT NULL,
    last_price TEXT NOT NULL,
    market_value TEXT NOT NULL,
    unrealized_pnl TEXT NOT NULL,
    PRIMARY KEY (run_id, snapshot_index, symbol),
    FOREIGN KEY (run_id, snapshot_index)
        REFERENCES account_snapshots(run_id, snapshot_index)
);
"""


class SQLiteRunStore:
    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)

    def initialize_schema(self) -> None:
        self._ensure_parent_dir()
        with self._connect() as connection:
            connection.executescript(SCHEMA_SQL)

    def save_run(
        self,
        *,
        run_id: str,
        summary: TradingRunSummary,
        created_at: datetime | None = None,
    ) -> None:
        normalized_run_id = run_id.strip()
        if not normalized_run_id:
            raise ValueError("run_id must not be blank")

        self.initialize_schema()
        created = created_at or datetime.now(timezone.utc)

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO runs (
                    run_id,
                    created_at,
                    events_processed,
                    signal_count,
                    order_count,
                    fill_count,
                    snapshot_count,
                    final_cash,
                    final_gross_market_value,
                    final_equity,
                    realized_pnl,
                    unrealized_pnl
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_run_id,
                    _datetime_text(created),
                    summary.events_processed,
                    len(summary.signals),
                    len(summary.order_results),
                    len(summary.fills),
                    len(summary.account_snapshots),
                    _decimal_text(summary.account.cash),
                    _decimal_text(summary.account.gross_market_value),
                    _decimal_text(summary.account.equity),
                    _decimal_text(summary.account.pnl.realized),
                    _decimal_text(summary.account.pnl.unrealized),
                ),
            )
            self._save_signals(connection, normalized_run_id, summary.signals)
            self._save_orders(connection, normalized_run_id, summary.order_results)
            self._save_fills(connection, normalized_run_id, summary.fills)
            self._save_snapshots(
                connection,
                normalized_run_id,
                summary.account_snapshots,
            )

    def list_runs(self) -> list[dict[str, Any]]:
        self.initialize_schema()
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM runs ORDER BY rowid").fetchall()
        return [_row_dict(row) for row in rows]

    def load_run(self, run_id: str) -> dict[str, object]:
        self.initialize_schema()
        with self._connect() as connection:
            run = connection.execute(
                "SELECT * FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
            if run is None:
                raise KeyError(run_id)
            signals = connection.execute(
                "SELECT * FROM signals WHERE run_id = ? ORDER BY signal_index",
                (run_id,),
            ).fetchall()
            orders = connection.execute(
                "SELECT * FROM orders WHERE run_id = ? ORDER BY rowid",
                (run_id,),
            ).fetchall()
            fills = connection.execute(
                "SELECT * FROM fills WHERE run_id = ? ORDER BY rowid",
                (run_id,),
            ).fetchall()
            account_snapshots = connection.execute(
                """
                SELECT * FROM account_snapshots
                WHERE run_id = ?
                ORDER BY snapshot_index
                """,
                (run_id,),
            ).fetchall()
            snapshot_positions = connection.execute(
                """
                SELECT * FROM snapshot_positions
                WHERE run_id = ?
                ORDER BY snapshot_index, symbol
                """,
                (run_id,),
            ).fetchall()

        return {
            "run": _row_dict(run),
            "signals": [_row_dict(row) for row in signals],
            "orders": [_row_dict(row) for row in orders],
            "fills": [_row_dict(row) for row in fills],
            "account_snapshots": [_row_dict(row) for row in account_snapshots],
            "snapshot_positions": [_row_dict(row) for row in snapshot_positions],
        }

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _ensure_parent_dir(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def _save_signals(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        signals: list[StrategySignal],
    ) -> None:
        connection.executemany(
            """
            INSERT INTO signals (
                run_id,
                signal_index,
                symbol,
                side,
                order_type,
                quantity,
                reference_price
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    index,
                    str(signal.symbol),
                    signal.side.value,
                    signal.order_type.value,
                    _decimal_text(signal.quantity),
                    _decimal_text(signal.reference_price),
                )
                for index, signal in enumerate(signals)
            ],
        )

    def _save_orders(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        order_results: list[OrderSubmissionResult],
    ) -> None:
        connection.executemany(
            """
            INSERT INTO orders (
                run_id,
                order_id,
                symbol,
                side,
                order_type,
                quantity,
                limit_price,
                filled_quantity,
                status,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                _order_values(run_id, result.order)
                for result in order_results
            ],
        )

    def _save_fills(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        fills: list[Fill],
    ) -> None:
        connection.executemany(
            """
            INSERT INTO fills (
                run_id,
                fill_id,
                order_id,
                symbol,
                side,
                price,
                quantity,
                notional,
                timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [_fill_values(run_id, fill) for fill in fills],
        )

    def _save_snapshots(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        snapshots: list[AccountSnapshot],
    ) -> None:
        for index, snapshot in enumerate(snapshots):
            connection.execute(
                """
                INSERT INTO account_snapshots (
                    run_id,
                    snapshot_index,
                    cash,
                    gross_market_value,
                    equity,
                    realized_pnl,
                    unrealized_pnl
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    index,
                    _decimal_text(snapshot.cash),
                    _decimal_text(snapshot.gross_market_value),
                    _decimal_text(snapshot.equity),
                    _decimal_text(snapshot.pnl.realized),
                    _decimal_text(snapshot.pnl.unrealized),
                ),
            )
            self._save_snapshot_positions(connection, run_id, index, snapshot)

    def _save_snapshot_positions(
        self,
        connection: sqlite3.Connection,
        run_id: str,
        snapshot_index: int,
        snapshot: AccountSnapshot,
    ) -> None:
        connection.executemany(
            """
            INSERT INTO snapshot_positions (
                run_id,
                snapshot_index,
                symbol,
                quantity,
                average_cost,
                last_price,
                market_value,
                unrealized_pnl
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                _position_values(run_id, snapshot_index, position)
                for position in sorted(
                    snapshot.positions.values(),
                    key=lambda item: str(item.symbol),
                )
            ],
        )


def _order_values(run_id: str, order: Order) -> tuple[object, ...]:
    return (
        run_id,
        order.order_id,
        str(order.symbol),
        order.side.value,
        order.order_type.value,
        _decimal_text(order.quantity),
        _optional_decimal_text(order.limit_price),
        _decimal_text(order.filled_quantity),
        order.status.value,
        _optional_datetime_text(order.created_at),
    )


def _fill_values(run_id: str, fill: Fill) -> tuple[object, ...]:
    return (
        run_id,
        fill.fill_id,
        fill.order_id,
        str(fill.symbol),
        fill.side.value,
        _decimal_text(fill.price),
        _decimal_text(fill.quantity),
        _decimal_text(fill.notional),
        _datetime_text(fill.timestamp),
    )


def _position_values(
    run_id: str,
    snapshot_index: int,
    position: Position,
) -> tuple[object, ...]:
    return (
        run_id,
        snapshot_index,
        str(position.symbol),
        _decimal_text(position.quantity),
        _decimal_text(position.average_cost),
        _decimal_text(position.last_price),
        _decimal_text(position.market_value),
        _decimal_text(position.unrealized_pnl),
    )


def _decimal_text(value: Decimal) -> str:
    return str(value)


def _optional_decimal_text(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_text(value)


def _datetime_text(value: datetime) -> str:
    return value.isoformat()


def _optional_datetime_text(value: datetime | None) -> str | None:
    if value is None:
        return None
    return _datetime_text(value)


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)
