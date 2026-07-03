from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from mini_trading.brokers.base import BrokerResult
from mini_trading.core.enums import OrderSide, OrderStatus, OrderType
from mini_trading.core.models import Fill, Order, Symbol


class MockBroker:
    def __init__(
        self,
        *,
        partial_fill_ratio: Decimal | None = None,
        reject_symbols: set[Symbol] | None = None,
    ) -> None:
        if partial_fill_ratio is not None and not (
            Decimal("0") < partial_fill_ratio <= Decimal("1")
        ):
            raise ValueError("partial_fill_ratio must be in (0, 1]")
        self._partial_fill_ratio = partial_fill_ratio
        self._reject_symbols = reject_symbols or set()
        self._fill_sequence = 0

    def submit_order(self, order: Order, *, market_price: Decimal) -> BrokerResult:
        if order.symbol in self._reject_symbols:
            return BrokerResult(
                status=OrderStatus.REJECTED,
                fills=[],
                reject_reason="broker rejected symbol",
            )

        if order.order_type is OrderType.LIMIT and not self._limit_can_fill(
            order, market_price
        ):
            return BrokerResult(status=OrderStatus.SUBMITTED, fills=[])

        fill_quantity = order.quantity
        status = OrderStatus.FILLED
        if self._partial_fill_ratio is not None:
            fill_quantity = order.quantity * self._partial_fill_ratio
            if fill_quantity < order.quantity:
                status = OrderStatus.PARTIALLY_FILLED

        fill = Fill(
            fill_id=self._next_fill_id(order),
            order_id=order.order_id,
            symbol=order.symbol,
            side=order.side,
            price=market_price,
            quantity=fill_quantity,
            timestamp=datetime.now(timezone.utc),
        )
        return BrokerResult(status=status, fills=[fill])

    def _limit_can_fill(self, order: Order, market_price: Decimal) -> bool:
        if order.limit_price is None:
            return False
        if order.side is OrderSide.BUY:
            return market_price <= order.limit_price
        return market_price >= order.limit_price

    def _next_fill_id(self, order: Order) -> str:
        self._fill_sequence += 1
        return f"{order.order_id}-fill-{self._fill_sequence}"

