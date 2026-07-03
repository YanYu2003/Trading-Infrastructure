from dataclasses import replace

from mini_trading.core.enums import OrderStatus
from mini_trading.core.models import Order


VALID_ORDER_TRANSITIONS: dict[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.CREATED: frozenset(
        {
            OrderStatus.SUBMITTED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        }
    ),
    OrderStatus.SUBMITTED: frozenset(
        {
            OrderStatus.PARTIALLY_FILLED,
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        }
    ),
    OrderStatus.PARTIALLY_FILLED: frozenset(
        {
            OrderStatus.FILLED,
            OrderStatus.CANCELLED,
        }
    ),
    OrderStatus.FILLED: frozenset(),
    OrderStatus.CANCELLED: frozenset(),
    OrderStatus.REJECTED: frozenset(),
}


class InvalidOrderTransition(ValueError):
    pass


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    return target in VALID_ORDER_TRANSITIONS[current]


def assert_transition(current: OrderStatus, target: OrderStatus) -> None:
    if not can_transition(current, target):
        raise InvalidOrderTransition(
            f"invalid order transition: {current.value} -> {target.value}"
        )


def transition_order(order: Order, target: OrderStatus) -> Order:
    assert_transition(order.status, target)
    return replace(order, status=target)

