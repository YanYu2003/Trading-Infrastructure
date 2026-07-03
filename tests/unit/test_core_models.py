from datetime import datetime, timezone
from decimal import Decimal

import pytest

from mini_trading.core.enums import (
    MarketDataEventType,
    OrderSide,
    OrderStatus,
    OrderType,
)
from mini_trading.core.models import (
    AccountSnapshot,
    Fill,
    MarketDataEvent,
    Order,
    PnL,
    Position,
    Quote,
    Symbol,
    Trade,
)


def test_symbol_normalizes_ticker_to_uppercase():
    symbol = Symbol("aapl")

    assert symbol.ticker == "AAPL"
    assert str(symbol) == "AAPL"


def test_symbol_rejects_blank_ticker():
    with pytest.raises(ValueError, match="ticker"):
        Symbol(" ")


def test_quote_requires_positive_bid_and_ask_with_bid_not_above_ask():
    symbol = Symbol("AAPL")
    quote = Quote(
        symbol=symbol,
        bid=Decimal("100.10"),
        ask=Decimal("100.20"),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert quote.spread == Decimal("0.10")

    with pytest.raises(ValueError, match="bid.*ask"):
        Quote(
            symbol=symbol,
            bid=Decimal("100.30"),
            ask=Decimal("100.20"),
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_trade_requires_positive_price_and_quantity():
    trade = Trade(
        symbol=Symbol("MSFT"),
        price=Decimal("250.50"),
        quantity=Decimal("25"),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert trade.notional == Decimal("6262.50")

    with pytest.raises(ValueError, match="price"):
        Trade(
            symbol=Symbol("MSFT"),
            price=Decimal("0"),
            quantity=Decimal("25"),
            timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_market_data_event_wraps_quote_or_trade_payload():
    trade = Trade(
        symbol=Symbol("AAPL"),
        price=Decimal("180.25"),
        quantity=Decimal("10"),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    event = MarketDataEvent(
        event_type=MarketDataEventType.TRADE,
        payload=trade,
        received_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert event.symbol == Symbol("AAPL")


def test_order_defaults_to_created_and_validates_limit_price():
    market_order = Order(
        order_id="ord-1",
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
    )

    assert market_order.status is OrderStatus.CREATED
    assert market_order.remaining_quantity == Decimal("10")

    with pytest.raises(ValueError, match="limit_price"):
        Order(
            order_id="ord-2",
            symbol=Symbol("AAPL"),
            side=OrderSide.BUY,
            order_type=OrderType.LIMIT,
            quantity=Decimal("10"),
        )


def test_fill_notional_and_position_market_value():
    fill = Fill(
        fill_id="fill-1",
        order_id="ord-1",
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        price=Decimal("180.25"),
        quantity=Decimal("10"),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    position = Position(
        symbol=Symbol("AAPL"),
        quantity=Decimal("10"),
        average_cost=Decimal("180.25"),
        last_price=Decimal("181.00"),
    )

    assert fill.notional == Decimal("1802.50")
    assert position.market_value == Decimal("1810.00")
    assert position.unrealized_pnl == Decimal("7.50")


def test_account_snapshot_computes_equity_from_cash_and_positions():
    snapshot = AccountSnapshot(
        cash=Decimal("98197.50"),
        positions={
            Symbol("AAPL"): Position(
                symbol=Symbol("AAPL"),
                quantity=Decimal("10"),
                average_cost=Decimal("180.25"),
                last_price=Decimal("181.00"),
            )
        },
        pnl=PnL(realized=Decimal("0"), unrealized=Decimal("7.50")),
    )

    assert snapshot.gross_market_value == Decimal("1810.00")
    assert snapshot.equity == Decimal("100007.50")
