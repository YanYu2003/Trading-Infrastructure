from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from mini_trading.core.enums import OrderSide, OrderStatus, OrderType
from mini_trading.core.models import Order, Symbol
from mini_trading.core.order_state import (
    InvalidOrderTransition,
    assert_transition,
    can_transition,
    transition_order,
)


def test_created_order_can_be_submitted_rejected_or_cancelled():
    assert can_transition(OrderStatus.CREATED, OrderStatus.SUBMITTED) is True
    assert can_transition(OrderStatus.CREATED, OrderStatus.REJECTED) is True
    assert can_transition(OrderStatus.CREATED, OrderStatus.CANCELLED) is True


def test_submitted_order_can_fill_partially_fill_cancel_or_reject():
    assert can_transition(OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED) is True
    assert can_transition(OrderStatus.SUBMITTED, OrderStatus.FILLED) is True
    assert can_transition(OrderStatus.SUBMITTED, OrderStatus.CANCELLED) is True
    assert can_transition(OrderStatus.SUBMITTED, OrderStatus.REJECTED) is True


def test_partially_filled_order_can_fill_or_cancel():
    assert can_transition(OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED) is True
    assert can_transition(OrderStatus.PARTIALLY_FILLED, OrderStatus.CANCELLED) is True


@pytest.mark.parametrize(
    "terminal_status",
    [OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED],
)
def test_terminal_statuses_cannot_transition(terminal_status):
    assert can_transition(terminal_status, OrderStatus.SUBMITTED) is False
    assert can_transition(terminal_status, terminal_status) is False


def test_invalid_transition_raises_descriptive_error():
    with pytest.raises(InvalidOrderTransition, match="created -> filled"):
        assert_transition(OrderStatus.CREATED, OrderStatus.FILLED)


def test_transition_order_returns_new_order_with_updated_status():
    order = Order(
        order_id="ord-1",
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
    )

    submitted = transition_order(order, OrderStatus.SUBMITTED)

    assert order.status is OrderStatus.CREATED
    assert submitted.status is OrderStatus.SUBMITTED
    with pytest.raises(FrozenInstanceError):
        submitted.status = OrderStatus.FILLED

