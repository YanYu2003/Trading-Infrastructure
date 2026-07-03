from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from mini_trading.core.enums import MarketDataEventType, OrderSide, OrderStatus, OrderType
from mini_trading.core.models import MarketDataEvent, Symbol, Trade
from mini_trading.core.oms import OrderSubmissionResult
from mini_trading.strategies.base import StrategySignal


@dataclass
class PriceThresholdStrategy:
    symbol: Symbol
    buy_below: Decimal
    sell_above: Decimal
    quantity: Decimal
    has_position: bool = False
    pending_side: OrderSide | None = None

    def on_event(self, event: MarketDataEvent) -> StrategySignal | None:
        if event.event_type is not MarketDataEventType.TRADE:
            return None
        if event.symbol != self.symbol:
            return None
        if not isinstance(event.payload, Trade):
            return None
        if self.pending_side is not None:
            return None

        price = event.payload.price
        if not self.has_position and price < self.buy_below:
            self.pending_side = OrderSide.BUY
            return StrategySignal(
                symbol=self.symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=self.quantity,
                reference_price=price,
            )

        if self.has_position and price > self.sell_above:
            self.pending_side = OrderSide.SELL
            return StrategySignal(
                symbol=self.symbol,
                side=OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=self.quantity,
                reference_price=price,
            )

        return None

    def on_order_result(self, result: OrderSubmissionResult) -> None:
        if self.pending_side is None:
            return

        if result.order.status is OrderStatus.REJECTED:
            self.pending_side = None
            return

        if result.fills:
            if self.pending_side is OrderSide.BUY:
                self.has_position = True
            elif result.order.status is OrderStatus.FILLED:
                self.has_position = False
            self.pending_side = None
            return

        if result.order.status is not OrderStatus.SUBMITTED:
            self.pending_side = None
