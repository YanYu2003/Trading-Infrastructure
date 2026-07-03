from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Iterable

from mini_trading.core.enums import MarketDataEventType
from mini_trading.core.models import MarketDataEvent, Quote, Symbol, Trade


@dataclass(frozen=True)
class MockMarketDataProvider:
    events: tuple[MarketDataEvent, ...]

    @classmethod
    def from_payloads(
        cls,
        payloads: Iterable[Quote | Trade],
        *,
        received_at: datetime | None = None,
    ) -> "MockMarketDataProvider":
        events = []
        for payload in payloads:
            event_type = (
                MarketDataEventType.QUOTE
                if isinstance(payload, Quote)
                else MarketDataEventType.TRADE
            )
            events.append(
                MarketDataEvent(
                    event_type=event_type,
                    payload=payload,
                    received_at=received_at or payload.timestamp,
                )
            )
        return cls(events=tuple(events))

    @classmethod
    def from_trades(
        cls,
        *,
        symbol: Symbol,
        prices: Iterable[Decimal],
        quantity: Decimal,
        start_at: datetime,
    ) -> "MockMarketDataProvider":
        trades = []
        for index, price in enumerate(prices):
            trades.append(
                Trade(
                    symbol=symbol,
                    price=price,
                    quantity=quantity,
                    timestamp=start_at + timedelta(seconds=index),
                )
            )
        return cls.from_payloads(trades)

    def stream(self) -> Iterable[MarketDataEvent]:
        return iter(self.events)

