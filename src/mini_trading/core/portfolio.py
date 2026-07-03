from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal

from mini_trading.core.enums import OrderSide
from mini_trading.core.models import AccountSnapshot, Fill, PnL, Position, Symbol


@dataclass(frozen=True)
class Portfolio:
    cash: Decimal
    positions: dict[Symbol, Position] = field(default_factory=dict)
    realized_pnl: Decimal = Decimal("0")

    def apply_fill(self, fill: Fill) -> "Portfolio":
        if fill.side is OrderSide.BUY:
            return self._apply_buy(fill)
        return self._apply_sell(fill)

    def mark_price(self, symbol: Symbol, price: Decimal) -> "Portfolio":
        if price < 0:
            raise ValueError("price must not be negative")
        position = self.positions.get(symbol)
        if position is None:
            return self
        positions = dict(self.positions)
        positions[symbol] = replace(position, last_price=price)
        return replace(self, positions=positions)

    def snapshot(self) -> AccountSnapshot:
        unrealized = sum(
            (position.unrealized_pnl for position in self.positions.values()),
            Decimal("0"),
        )
        return AccountSnapshot(
            cash=self.cash,
            positions=dict(self.positions),
            pnl=PnL(realized=self.realized_pnl, unrealized=unrealized),
        )

    def _apply_buy(self, fill: Fill) -> "Portfolio":
        position = self.positions.get(fill.symbol)
        if position is None:
            new_position = Position(
                symbol=fill.symbol,
                quantity=fill.quantity,
                average_cost=fill.price,
                last_price=fill.price,
            )
        else:
            new_quantity = position.quantity + fill.quantity
            total_cost = position.quantity * position.average_cost + fill.notional
            new_position = Position(
                symbol=fill.symbol,
                quantity=new_quantity,
                average_cost=total_cost / new_quantity,
                last_price=fill.price,
            )

        positions = dict(self.positions)
        positions[fill.symbol] = new_position
        return replace(self, cash=self.cash - fill.notional, positions=positions)

    def _apply_sell(self, fill: Fill) -> "Portfolio":
        position = self.positions.get(fill.symbol)
        if position is None or fill.quantity > position.quantity:
            raise ValueError("sell quantity exceeds position")

        remaining_quantity = position.quantity - fill.quantity
        realized_delta = (fill.price - position.average_cost) * fill.quantity
        positions = dict(self.positions)
        if remaining_quantity == 0:
            positions.pop(fill.symbol)
        else:
            positions[fill.symbol] = Position(
                symbol=fill.symbol,
                quantity=remaining_quantity,
                average_cost=position.average_cost,
                last_price=fill.price,
            )

        return replace(
            self,
            cash=self.cash + fill.notional,
            positions=positions,
            realized_pnl=self.realized_pnl + realized_delta,
        )

