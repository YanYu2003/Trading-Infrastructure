from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from mini_trading.core.enums import OrderStatus
from mini_trading.core.models import Fill, Order


@dataclass(frozen=True)
class BrokerResult:
    status: OrderStatus
    fills: list[Fill]
    reject_reason: str | None = None


class BrokerAdapter(Protocol):
    def submit_order(self, order: Order, *, market_price: Decimal) -> BrokerResult:
        raise NotImplementedError

