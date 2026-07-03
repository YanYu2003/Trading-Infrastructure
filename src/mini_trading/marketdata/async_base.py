from __future__ import annotations

from typing import AsyncIterator, Protocol

from mini_trading.core.models import MarketDataEvent


class AsyncMarketDataProvider(Protocol):
    def stream(self) -> AsyncIterator[MarketDataEvent]:
        raise NotImplementedError
