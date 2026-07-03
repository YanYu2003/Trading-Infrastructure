from datetime import datetime, timezone
from decimal import Decimal

from mini_trading.core.enums import MarketDataEventType
from mini_trading.core.models import Quote, Symbol, Trade
from mini_trading.marketdata.mock import MockMarketDataProvider


def test_mock_provider_yields_deterministic_trade_events():
    provider = MockMarketDataProvider.from_trades(
        symbol=Symbol("AAPL"),
        prices=[Decimal("100"), Decimal("101")],
        quantity=Decimal("10"),
        start_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    events = list(provider.stream())

    assert [event.event_type for event in events] == [
        MarketDataEventType.TRADE,
        MarketDataEventType.TRADE,
    ]
    assert [event.payload.price for event in events] == [
        Decimal("100"),
        Decimal("101"),
    ]
    assert all(isinstance(event.payload, Trade) for event in events)


def test_mock_provider_yields_quote_events():
    quote = Quote(
        symbol=Symbol("AAPL"),
        bid=Decimal("99.95"),
        ask=Decimal("100.05"),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    provider = MockMarketDataProvider.from_payloads([quote])

    events = list(provider.stream())

    assert len(events) == 1
    assert events[0].event_type is MarketDataEventType.QUOTE
    assert events[0].payload.spread == Decimal("0.10")


def test_mock_provider_preserves_event_order_and_is_reiterable():
    provider = MockMarketDataProvider.from_trades(
        symbol=Symbol("MSFT"),
        prices=[Decimal("200"), Decimal("199"), Decimal("201")],
        quantity=Decimal("5"),
        start_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    first_pass = list(provider.stream())
    second_pass = list(provider.stream())

    assert [event.payload.price for event in first_pass] == [
        Decimal("200"),
        Decimal("199"),
        Decimal("201"),
    ]
    assert first_pass == second_pass

