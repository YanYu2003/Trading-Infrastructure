from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

from mini_trading.core.enums import OrderSide, OrderType
from mini_trading.core.models import MarketDataEvent, Symbol


@dataclass(frozen=True)
class StrategySignal:
    symbol: Symbol
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    reference_price: Decimal


class Strategy(Protocol):
    def on_event(self, event: MarketDataEvent) -> StrategySignal | None:
        raise NotImplementedError

