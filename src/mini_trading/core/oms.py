from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal

from mini_trading.brokers.base import BrokerAdapter, BrokerResult
from mini_trading.core.enums import OrderSide, OrderStatus, OrderType
from mini_trading.core.models import Fill, Order, Symbol
from mini_trading.core.order_state import transition_order
from mini_trading.core.portfolio import Portfolio
from mini_trading.core.risk import RiskCheckResult, RiskEngine


@dataclass(frozen=True)
class OrderSubmissionResult:
    order: Order
    risk_result: RiskCheckResult
    broker_result: BrokerResult | None
    fills: list[Fill]


class OrderManager:
    def __init__(
        self,
        *,
        portfolio: Portfolio,
        risk_engine: RiskEngine,
        broker: BrokerAdapter,
    ) -> None:
        self.portfolio = portfolio
        self._risk_engine = risk_engine
        self._broker = broker
        self._orders: dict[str, Order] = {}
        self._fills: list[Fill] = []
        self._order_sequence = 0

    @property
    def orders(self) -> dict[str, Order]:
        return dict(self._orders)

    @property
    def fills(self) -> list[Fill]:
        return list(self._fills)

    def submit_order(
        self,
        *,
        symbol: Symbol,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        market_price: Decimal,
        limit_price: Decimal | None = None,
    ) -> OrderSubmissionResult:
        order = Order(
            order_id=self._next_order_id(),
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            limit_price=limit_price,
        )
        self._orders[order.order_id] = order

        risk_result = self._risk_engine.check_order(
            order,
            account=self.portfolio.snapshot(),
            reference_price=market_price,
            open_orders=self._orders.values(),
        )
        if not risk_result.allowed:
            rejected = transition_order(order, OrderStatus.REJECTED)
            self._orders[rejected.order_id] = rejected
            return OrderSubmissionResult(
                order=rejected,
                risk_result=risk_result,
                broker_result=None,
                fills=[],
            )

        submitted = transition_order(order, OrderStatus.SUBMITTED)
        self._orders[submitted.order_id] = submitted

        broker_result = self._broker.submit_order(submitted, market_price=market_price)
        final_order = self._apply_broker_result(submitted, broker_result)
        self._orders[final_order.order_id] = final_order

        for fill in broker_result.fills:
            self.portfolio = self.portfolio.apply_fill(fill)
            self._fills.append(fill)

        return OrderSubmissionResult(
            order=final_order,
            risk_result=risk_result,
            broker_result=broker_result,
            fills=list(broker_result.fills),
        )

    def cancel_order(self, order_id: str) -> Order:
        order = self._orders[order_id]
        cancelled = transition_order(order, OrderStatus.CANCELLED)
        self._orders[order_id] = cancelled
        return cancelled

    def _apply_broker_result(
        self, order: Order, broker_result: BrokerResult
    ) -> Order:
        filled_quantity = sum(
            (fill.quantity for fill in broker_result.fills),
            Decimal("0"),
        )
        updated_order = replace(order, filled_quantity=filled_quantity)
        if broker_result.status is OrderStatus.SUBMITTED:
            return updated_order
        return transition_order(updated_order, broker_result.status)

    def _next_order_id(self) -> str:
        self._order_sequence += 1
        return f"ord-{self._order_sequence}"
