from datetime import datetime, timezone
from decimal import Decimal

import pytest

from mini_trading.brokers.mock import MockBroker
from mini_trading.core.async_engine import AsyncTradingEngine
from mini_trading.core.models import Symbol
from mini_trading.core.oms import OrderManager
from mini_trading.core.portfolio import Portfolio
from mini_trading.core.risk import RiskEngine, RiskLimits
from mini_trading.marketdata.async_mock import AsyncMockMarketDataProvider
from mini_trading.strategies.threshold import PriceThresholdStrategy


def _async_engine() -> AsyncTradingEngine:
    symbol = Symbol("AAPL")
    provider = AsyncMockMarketDataProvider.from_trades(
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
    return AsyncTradingEngine(
        market_data=provider,
        strategy=strategy,
        order_manager=manager,
    )


@pytest.mark.asyncio
async def test_async_trading_engine_matches_sync_demo_summary():
    summary = await _async_engine().run()

    assert summary.events_processed == 4
    assert len(summary.signals) == 2
    assert len(summary.order_results) == 2
    assert len(summary.fills) == 2
    assert summary.account.cash == Decimal("100120")
    assert summary.account.equity == Decimal("100120")


@pytest.mark.asyncio
async def test_async_market_data_provider_is_reiterable():
    symbol = Symbol("AAPL")
    provider = AsyncMockMarketDataProvider.from_trades(
        symbol=symbol,
        prices=[Decimal("101"), Decimal("102")],
        quantity=Decimal("10"),
        start_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    first = [event async for event in provider.stream()]
    second = [event async for event in provider.stream()]

    assert [event.payload.price for event in first] == [Decimal("101"), Decimal("102")]
    assert [event.payload.price for event in second] == [Decimal("101"), Decimal("102")]
