from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import sys

from mini_trading.brokers.mock import MockBroker
from mini_trading.core.engine import TradingEngine, TradingRunSummary
from mini_trading.core.models import Symbol
from mini_trading.core.oms import OrderManager
from mini_trading.core.portfolio import Portfolio
from mini_trading.core.risk import RiskEngine, RiskLimits
from mini_trading.marketdata.mock import MockMarketDataProvider
from mini_trading.persistence.sqlite import SQLiteRunStore
from mini_trading.reports.replay import ReplayReport
from mini_trading.strategies.threshold import PriceThresholdStrategy


def build_demo_engine() -> TradingEngine:
    symbol = Symbol("AAPL")
    market_data = MockMarketDataProvider.from_trades(
        symbol=symbol,
        prices=[
            Decimal("105"),
            Decimal("99"),
            Decimal("106"),
            Decimal("111"),
        ],
        quantity=Decimal("10"),
        start_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    order_manager = OrderManager(
        portfolio=Portfolio(cash=Decimal("100000")),
        risk_engine=RiskEngine(
            RiskLimits(
                max_order_notional=Decimal("10000"),
                max_position_quantity=Decimal("100"),
            )
        ),
        broker=MockBroker(),
    )
    strategy = PriceThresholdStrategy(
        symbol=symbol,
        buy_below=Decimal("100"),
        sell_above=Decimal("110"),
        quantity=Decimal("10"),
    )
    return TradingEngine(
        market_data=market_data,
        strategy=strategy,
        order_manager=order_manager,
    )


def run_demo() -> TradingRunSummary:
    return build_demo_engine().run()


def write_demo_reports(output_dir: str | Path) -> list[Path]:
    summary = run_demo()
    report = ReplayReport.from_summary(summary)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    files = {
        "summary.json": report.to_json(),
        "orders.csv": report.orders_csv(),
        "fills.csv": report.fills_csv(),
        "account_snapshots.csv": report.account_snapshots_csv(),
    }
    written = []
    for filename, content in files.items():
        path = output_path / filename
        path.write_text(content, encoding="utf-8")
        written.append(path)
    return written


def write_demo_sqlite(db_path: str | Path, run_id: str = "demo") -> Path:
    summary = run_demo()
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    SQLiteRunStore(path).save_run(run_id=run_id, summary=summary)
    return path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the deterministic trading demo.")
    parser.add_argument(
        "output_dir",
        nargs="?",
        help="Optional directory for JSON and CSV replay reports.",
    )
    parser.add_argument(
        "--sqlite",
        dest="sqlite_path",
        help="Optional SQLite database path for persisted run history.",
    )
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    summary = run_demo()
    print(f"events_processed={summary.events_processed}")
    print(f"signals={len(summary.signals)}")
    print(f"orders={len(summary.order_results)}")
    print(f"fills={len(summary.fills)}")
    print(f"cash={summary.account.cash}")
    print(f"equity={summary.account.equity}")
    print(f"realized_pnl={summary.account.pnl.realized}")
    print(f"unrealized_pnl={summary.account.pnl.unrealized}")
    if args.output_dir:
        written = write_demo_reports(args.output_dir)
        for path in written:
            print(f"wrote={path}")
    if args.sqlite_path:
        written_sqlite = write_demo_sqlite(args.sqlite_path)
        print(f"wrote_sqlite={written_sqlite}")


if __name__ == "__main__":
    main()
