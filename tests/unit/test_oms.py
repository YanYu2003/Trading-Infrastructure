from decimal import Decimal

import pytest

from mini_trading.brokers.mock import MockBroker
from mini_trading.core.enums import OrderSide, OrderStatus, OrderType
from mini_trading.core.oms import OrderManager
from mini_trading.core.order_state import InvalidOrderTransition
from mini_trading.core.portfolio import Portfolio
from mini_trading.core.risk import RiskEngine, RiskLimits
from mini_trading.core.models import Symbol


def test_order_manager_rejects_order_before_broker_when_risk_fails():
    manager = OrderManager(
        portfolio=Portfolio(cash=Decimal("100")),
        risk_engine=RiskEngine(),
        broker=MockBroker(),
    )

    result = manager.submit_order(
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        market_price=Decimal("100"),
    )

    assert result.order.status is OrderStatus.REJECTED
    assert result.risk_result.allowed is False
    assert result.broker_result is None
    assert result.fills == []
    assert manager.portfolio.cash == Decimal("100")


def test_order_manager_fills_market_order_and_updates_portfolio():
    manager = OrderManager(
        portfolio=Portfolio(cash=Decimal("100000")),
        risk_engine=RiskEngine(RiskLimits(max_order_notional=Decimal("5000"))),
        broker=MockBroker(),
    )

    result = manager.submit_order(
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        market_price=Decimal("100"),
    )

    assert result.order.status is OrderStatus.FILLED
    assert result.order.filled_quantity == Decimal("10")
    assert result.order.remaining_quantity == Decimal("0")
    assert len(result.fills) == 1
    assert manager.portfolio.cash == Decimal("99000")
    assert manager.portfolio.positions[Symbol("AAPL")].quantity == Decimal("10")


def test_order_manager_keeps_limit_order_submitted_when_not_filled():
    manager = OrderManager(
        portfolio=Portfolio(cash=Decimal("100000")),
        risk_engine=RiskEngine(),
        broker=MockBroker(),
    )

    result = manager.submit_order(
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("10"),
        limit_price=Decimal("99"),
        market_price=Decimal("100"),
    )

    assert result.order.status is OrderStatus.SUBMITTED
    assert result.order.filled_quantity == Decimal("0")
    assert result.fills == []
    assert manager.portfolio.cash == Decimal("100000")


def test_order_manager_records_partial_fill_status_and_quantity():
    manager = OrderManager(
        portfolio=Portfolio(cash=Decimal("100000")),
        risk_engine=RiskEngine(),
        broker=MockBroker(partial_fill_ratio=Decimal("0.4")),
    )

    result = manager.submit_order(
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        market_price=Decimal("100"),
    )

    assert result.order.status is OrderStatus.PARTIALLY_FILLED
    assert result.order.filled_quantity == Decimal("4.0")
    assert result.order.remaining_quantity == Decimal("6.0")
    assert manager.portfolio.cash == Decimal("99600.0")
    assert manager.portfolio.positions[Symbol("AAPL")].quantity == Decimal("4.0")


def test_order_manager_records_broker_rejection_without_portfolio_update():
    manager = OrderManager(
        portfolio=Portfolio(cash=Decimal("100000")),
        risk_engine=RiskEngine(),
        broker=MockBroker(reject_symbols={Symbol("AAPL")}),
    )

    result = manager.submit_order(
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        market_price=Decimal("100"),
    )

    assert result.order.status is OrderStatus.REJECTED
    assert result.broker_result is not None
    assert result.broker_result.reject_reason == "broker rejected symbol"
    assert result.fills == []
    assert manager.portfolio.cash == Decimal("100000")


def test_order_manager_cancels_submitted_limit_order_without_portfolio_update():
    manager = OrderManager(
        portfolio=Portfolio(cash=Decimal("100000")),
        risk_engine=RiskEngine(),
        broker=MockBroker(),
    )
    submitted = manager.submit_order(
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=Decimal("10"),
        limit_price=Decimal("99"),
        market_price=Decimal("100"),
    )

    cancelled = manager.cancel_order(submitted.order.order_id)

    assert cancelled.status is OrderStatus.CANCELLED
    assert manager.orders[submitted.order.order_id].status is OrderStatus.CANCELLED
    assert manager.portfolio.cash == Decimal("100000")


def test_order_manager_cannot_cancel_filled_order():
    manager = OrderManager(
        portfolio=Portfolio(cash=Decimal("100000")),
        risk_engine=RiskEngine(),
        broker=MockBroker(),
    )
    filled = manager.submit_order(
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        market_price=Decimal("100"),
    )

    with pytest.raises(InvalidOrderTransition, match="filled -> cancelled"):
        manager.cancel_order(filled.order.order_id)
