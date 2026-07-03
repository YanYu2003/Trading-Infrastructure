from __future__ import annotations

import argparse
import csv
from io import StringIO
from pathlib import Path
import sys
from typing import Any

from mini_trading.persistence.sqlite import SQLiteRunStore


LIST_RUNS_FIELDS = [
    "run_id",
    "events_processed",
    "signal_count",
    "order_count",
    "fill_count",
    "snapshot_count",
    "final_equity",
    "realized_pnl",
    "unrealized_pnl",
]

SHOW_RUN_FIELDS = [
    "run_id",
    "created_at",
    "events_processed",
    "signal_count",
    "order_count",
    "fill_count",
    "snapshot_count",
    "final_cash",
    "final_gross_market_value",
    "final_equity",
    "realized_pnl",
    "unrealized_pnl",
]

ORDER_FIELDS = [
    "order_id",
    "symbol",
    "side",
    "order_type",
    "quantity",
    "limit_price",
    "filled_quantity",
    "status",
    "created_at",
]

FILL_FIELDS = [
    "fill_id",
    "order_id",
    "symbol",
    "side",
    "price",
    "quantity",
    "notional",
    "timestamp",
]

SNAPSHOT_FIELDS = [
    "snapshot_index",
    "cash",
    "gross_market_value",
    "equity",
    "realized_pnl",
    "unrealized_pnl",
]

POSITION_FIELDS = [
    "snapshot_index",
    "symbol",
    "quantity",
    "average_cost",
    "last_price",
    "market_value",
    "unrealized_pnl",
]


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    store = SQLiteRunStore(Path(args.database))

    if args.command == "list-runs":
        _print_rows(LIST_RUNS_FIELDS, store.list_runs())
        return

    loaded = store.load_run(args.run_id)
    if args.command == "show-run":
        _print_rows(SHOW_RUN_FIELDS, [loaded["run"]])
    elif args.command == "orders":
        _print_rows(ORDER_FIELDS, loaded["orders"])
    elif args.command == "fills":
        _print_rows(FILL_FIELDS, loaded["fills"])
    elif args.command == "snapshots":
        _print_rows(SNAPSHOT_FIELDS, loaded["account_snapshots"])
    elif args.command == "positions":
        rows = list(loaded["snapshot_positions"])
        if args.snapshot_index is not None:
            rows = [
                row
                for row in rows
                if row["snapshot_index"] == args.snapshot_index
            ]
        _print_rows(POSITION_FIELDS, rows)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect persisted mini trading run history.",
    )
    parser.add_argument("database", help="SQLite database path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-runs", help="List persisted trading runs.")

    show_run = subparsers.add_parser("show-run", help="Show one run summary.")
    show_run.add_argument("run_id")

    orders = subparsers.add_parser("orders", help="Show persisted order rows.")
    orders.add_argument("run_id")

    fills = subparsers.add_parser("fills", help="Show persisted fill rows.")
    fills.add_argument("run_id")

    snapshots = subparsers.add_parser(
        "snapshots",
        help="Show persisted account snapshot rows.",
    )
    snapshots.add_argument("run_id")

    positions = subparsers.add_parser(
        "positions",
        help="Show persisted snapshot position rows.",
    )
    positions.add_argument("run_id")
    positions.add_argument("--snapshot-index", type=int)

    return parser


def _print_rows(fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    print(_csv_text(fieldnames, rows), end="")


def _csv_text(fieldnames: list[str], rows: list[dict[str, Any]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    writer.writerows(_select_fields(rows, fieldnames))
    return output.getvalue()


def _select_fields(
    rows: list[dict[str, Any]],
    fieldnames: list[str],
) -> list[dict[str, Any]]:
    return [
        {
            fieldname: row.get(fieldname, "")
            for fieldname in fieldnames
        }
        for row in rows
    ]


if __name__ == "__main__":
    main()
