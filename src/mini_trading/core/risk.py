from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable

from mini_trading.core.enums import OrderSide, OrderStatus
from mini_trading.core.models import AccountSnapshot, Order


OPEN_ORDER_STATUSES = {
    OrderStatus.SUBMITTED,
    OrderStatus.PARTIALLY_FILLED,
}


@dataclass(frozen=True)
class RiskLimits:
    max_order_notional: Decimal | None = None
    max_position_quantity: Decimal | None = None
    reject_duplicate_open_orders: bool = True
    kill_switch_enabled: bool = False


@dataclass(frozen=True)
class RiskCheckResult:
    allowed: bool
    reason: str | None = None

    @classmethod
    def allow(cls) -> "RiskCheckResult":
        return cls(allowed=True)

    @classmethod
    def reject(cls, reason: str) -> "RiskCheckResult":
        return cls(allowed=False, reason=reason)


class RiskEngine:
    def __init__(self, limits: RiskLimits | None = None) -> None:
        self._limits = limits or RiskLimits()

    def check_order(
        self,
        order: Order,
        *,
        account: AccountSnapshot,
        reference_price: Decimal,
        open_orders: Iterable[Order] = (),
    ) -> RiskCheckResult:
        if self._limits.kill_switch_enabled:
            return RiskCheckResult.reject("kill switch enabled")

        notional = order.quantity * reference_price
        if (
            self._limits.max_order_notional is not None
            and notional > self._limits.max_order_notional
        ):
            return RiskCheckResult.reject("order notional exceeds limit")

        current_position = account.positions.get(order.symbol)
        current_quantity = (
            current_position.quantity if current_position is not None else Decimal("0")
        )

        if order.side is OrderSide.BUY:
            if notional > account.cash:
                return RiskCheckResult.reject("insufficient cash")
            if (
                self._limits.max_position_quantity is not None
                and current_quantity + order.quantity
                > self._limits.max_position_quantity
            ):
                return RiskCheckResult.reject("position limit exceeded")
        else:
            if order.quantity > current_quantity:
                return RiskCheckResult.reject("sell quantity exceeds position")

        if self._limits.reject_duplicate_open_orders:
            for open_order in open_orders:
                if (
                    open_order.order_id != order.order_id
                    and open_order.symbol == order.symbol
                    and open_order.side is order.side
                    and open_order.status in OPEN_ORDER_STATUSES
                ):
                    return RiskCheckResult.reject("duplicate open order")

        return RiskCheckResult.allow()

