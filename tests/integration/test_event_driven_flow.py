from datetime import datetime, timezone
from decimal import Decimal

from mini_trading.brokers.mock import MockBroker
from mini_trading.core.engine import TradingEngine
from mini_trading.core.models import Quote, Symbol
from mini_trading.core.portfolio import Portfolio
from mini_trading.core.risk import RiskEngine, RiskLimits
from mini_trading.core.oms import OrderManager
from mini_trading.marketdata.mock import MockMarketDataProvider
from mini_trading.strategies.threshold import PriceThresholdStrategy


def _engine_with_prices(prices: list[Decimal]) -> TradingEngine:
    symbol = Symbol("AAPL")
    provider = MockMarketDataProvider.from_trades(
        symbol=symbol,
        prices=prices,
        quantity=Decimal("10"),
        start_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    manager = OrderManager(
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
        market_data=provider,
        strategy=strategy,
        order_manager=manager,
    )


def test_event_driven_flow_triggers_buy_and_sell_orders():
    engine = _engine_with_prices(
        [Decimal("105"), Decimal("99"), Decimal("106"), Decimal("111")]
    )

    summary = engine.run()

    assert summary.events_processed == 4
    assert len(summary.account_snapshots) == 4
    assert len(summary.signals) == 2
    assert len(summary.order_results) == 2
    assert len(summary.fills) == 2
    assert summary.account.cash == Decimal("100120")
    assert summary.account.positions == {}
    assert summary.account.pnl.realized == Decimal("120")
    assert summary.account.pnl.unrealized == Decimal("0")
    assert summary.account.equity == Decimal("100120")
    assert [snapshot.equity for snapshot in summary.account_snapshots] == [
        Decimal("100000"),
        Decimal("100000"),
        Decimal("100070"),
        Decimal("100120"),
    ]


def test_event_driven_flow_with_quote_only_stream_does_not_trade():
    symbol = Symbol("AAPL")
    quote = Quote(
        symbol=symbol,
        bid=Decimal("99"),
        ask=Decimal("99.05"),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    provider = MockMarketDataProvider.from_payloads([quote])
    manager = OrderManager(
        portfolio=Portfolio(cash=Decimal("100000")),
        risk_engine=RiskEngine(),
        broker=MockBroker(),
    )
    strategy = PriceThresholdStrategy(
        symbol=symbol,
        buy_below=Decimal("100"),
        sell_above=Decimal("110"),
        quantity=Decimal("10"),
    )
    engine = TradingEngine(
        market_data=provider,
        strategy=strategy,
        order_manager=manager,
    )

    summary = engine.run()

    assert summary.events_processed == 1
    assert len(summary.account_snapshots) == 1
    assert summary.signals == []
    assert summary.order_results == []
    assert summary.fills == []
    assert summary.account.cash == Decimal("100000")
