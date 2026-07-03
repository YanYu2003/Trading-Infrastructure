from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from mini_trading.core.enums import (
    MarketDataEventType,
    OrderSide,
    OrderStatus,
    OrderType,
)


def _require_positive(value: Decimal, field_name: str) -> None:
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


@dataclass(frozen=True)
class Symbol:
    ticker: str

    def __post_init__(self) -> None:
        ticker = self.ticker.strip().upper()
        if not ticker:
            raise ValueError("ticker must not be blank")
        object.__setattr__(self, "ticker", ticker)

    def __str__(self) -> str:
        return self.ticker


@dataclass(frozen=True)
class Quote:
    symbol: Symbol
    bid: Decimal
    ask: Decimal
    timestamp: datetime

    def __post_init__(self) -> None:
        _require_positive(self.bid, "bid")
        _require_positive(self.ask, "ask")
        if self.bid > self.ask:
            raise ValueError("bid must not be above ask")

    @property
    def spread(self) -> Decimal:
        return self.ask - self.bid


@dataclass(frozen=True)
class Trade:
    symbol: Symbol
    price: Decimal
    quantity: Decimal
    timestamp: datetime

    def __post_init__(self) -> None:
        _require_positive(self.price, "price")
        _require_positive(self.quantity, "quantity")

    @property
    def notional(self) -> Decimal:
        return self.price * self.quantity


@dataclass(frozen=True)
class MarketDataEvent:
    event_type: MarketDataEventType
    payload: Quote | Trade
    received_at: datetime

    @property
    def symbol(self) -> Symbol:
        return self.payload.symbol


@dataclass(frozen=True)
class Order:
    order_id: str
    symbol: Symbol
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    limit_price: Decimal | None = None
    status: OrderStatus = OrderStatus.CREATED
    filled_quantity: Decimal = Decimal("0")
    created_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.order_id.strip():
            raise ValueError("order_id must not be blank")
        _require_positive(self.quantity, "quantity")
        if self.filled_quantity < 0:
            raise ValueError("filled_quantity must not be negative")
        if self.filled_quantity > self.quantity:
            raise ValueError("filled_quantity must not exceed quantity")
        if self.order_type is OrderType.LIMIT:
            if self.limit_price is None:
                raise ValueError("limit_price is required for limit orders")
            _require_positive(self.limit_price, "limit_price")

    @property
    def remaining_quantity(self) -> Decimal:
        return self.quantity - self.filled_quantity


@dataclass(frozen=True)
class Fill:
    fill_id: str
    order_id: str
    symbol: Symbol
    side: OrderSide
    price: Decimal
    quantity: Decimal
    timestamp: datetime

    def __post_init__(self) -> None:
        if not self.fill_id.strip():
            raise ValueError("fill_id must not be blank")
        if not self.order_id.strip():
            raise ValueError("order_id must not be blank")
        _require_positive(self.price, "price")
        _require_positive(self.quantity, "quantity")

    @property
    def notional(self) -> Decimal:
        return self.price * self.quantity


@dataclass(frozen=True)
class Position:
    symbol: Symbol
    quantity: Decimal = Decimal("0")
    average_cost: Decimal = Decimal("0")
    last_price: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        if self.quantity < 0:
            raise ValueError("quantity must not be negative")
        if self.average_cost < 0:
            raise ValueError("average_cost must not be negative")
        if self.last_price < 0:
            raise ValueError("last_price must not be negative")

    @property
    def market_value(self) -> Decimal:
        return self.quantity * self.last_price

    @property
    def unrealized_pnl(self) -> Decimal:
        return (self.last_price - self.average_cost) * self.quantity


@dataclass(frozen=True)
class PnL:
    realized: Decimal = Decimal("0")
    unrealized: Decimal = Decimal("0")

    @property
    def total(self) -> Decimal:
        return self.realized + self.unrealized


@dataclass(frozen=True)
class AccountSnapshot:
    cash: Decimal
    positions: dict[Symbol, Position] = field(default_factory=dict)
    pnl: PnL = field(default_factory=PnL)

    @property
    def gross_market_value(self) -> Decimal:
        return sum(
            (position.market_value for position in self.positions.values()),
            Decimal("0"),
        )

    @property
    def equity(self) -> Decimal:
        return self.cash + self.gross_market_value

