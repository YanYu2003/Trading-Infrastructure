from decimal import Decimal

from mini_trading.brokers.mock import MockBroker
from mini_trading.core.enums import OrderSide, OrderStatus, OrderType
from mini_trading.core.models import Order, Symbol


def _order(
    *,
    order_id: str = "ord-1",
    side: OrderSide = OrderSide.BUY,
    order_type: OrderType = OrderType.MARKET,
    quantity: Decimal = Decimal("10"),
    limit_price: Decimal | None = None,
) -> Order:
    return Order(
        order_id=order_id,
        symbol=Symbol("AAPL"),
        side=side,
        order_type=order_type,
        quantity=quantity,
        limit_price=limit_price,
    )


def test_market_order_fills_at_market_price():
    broker = MockBroker()

    result = broker.submit_order(_order(), market_price=Decimal("101.25"))

    assert result.status is OrderStatus.FILLED
    assert result.reject_reason is None
    assert len(result.fills) == 1
    assert result.fills[0].price == Decimal("101.25")
    assert result.fills[0].quantity == Decimal("10")
    assert result.fills[0].order_id == "ord-1"


def test_limit_buy_does_not_fill_when_market_price_is_above_limit():
    broker = MockBroker()

    result = broker.submit_order(
        _order(order_type=OrderType.LIMIT, limit_price=Decimal("100")),
        market_price=Decimal("101"),
    )

    assert result.status is OrderStatus.SUBMITTED
    assert result.fills == []


def test_limit_buy_fills_when_market_price_is_at_or_below_limit():
    broker = MockBroker()

    result = broker.submit_order(
        _order(order_type=OrderType.LIMIT, limit_price=Decimal("100")),
        market_price=Decimal("99.50"),
    )

    assert result.status is OrderStatus.FILLED
    assert result.fills[0].price == Decimal("99.50")


def test_limit_sell_fills_when_market_price_is_at_or_above_limit():
    broker = MockBroker()

    result = broker.submit_order(
        _order(
            side=OrderSide.SELL,
            order_type=OrderType.LIMIT,
            limit_price=Decimal("100"),
        ),
        market_price=Decimal("100.50"),
    )

    assert result.status is OrderStatus.FILLED
    assert result.fills[0].price == Decimal("100.50")


def test_partial_fill_mode_returns_partially_filled_result():
    broker = MockBroker(partial_fill_ratio=Decimal("0.4"))

    result = broker.submit_order(
        _order(quantity=Decimal("10")),
        market_price=Decimal("100"),
    )

    assert result.status is OrderStatus.PARTIALLY_FILLED
    assert result.fills[0].quantity == Decimal("4.0")


def test_reject_mode_returns_broker_rejection_without_fills():
    broker = MockBroker(reject_symbols={Symbol("AAPL")})

    result = broker.submit_order(_order(), market_price=Decimal("100"))

    assert result.status is OrderStatus.REJECTED
    assert result.fills == []
    assert result.reject_reason == "broker rejected symbol"

