from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import AsyncIterator, Iterable

from mini_trading.core.enums import MarketDataEventType
from mini_trading.core.models import MarketDataEvent, Quote, Symbol, Trade


@dataclass(frozen=True)
class AsyncMockMarketDataProvider:
    events: tuple[MarketDataEvent, ...]
    delay_seconds: float = 0

    @classmethod
    def from_payloads(
        cls,
        payloads: Iterable[Quote | Trade],
        *,
        received_at: datetime | None = None,
        delay_seconds: float = 0,
    ) -> "AsyncMockMarketDataProvider":
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
        return cls(events=tuple(events), delay_seconds=delay_seconds)

    @classmethod
    def from_trades(
        cls,
        *,
        symbol: Symbol,
        prices: Iterable[Decimal],
        quantity: Decimal,
        start_at: datetime,
        delay_seconds: float = 0,
    ) -> "AsyncMockMarketDataProvider":
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
        return cls.from_payloads(trades, delay_seconds=delay_seconds)

    async def stream(self) -> AsyncIterator[MarketDataEvent]:
        for event in self.events:
            if self.delay_seconds > 0:
                await asyncio.sleep(self.delay_seconds)
            yield event
