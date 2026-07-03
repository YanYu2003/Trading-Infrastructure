from __future__ import annotations

from typing import Iterable, Protocol

from mini_trading.core.models import MarketDataEvent


class MarketDataProvider(Protocol):
    def stream(self) -> Iterable[MarketDataEvent]:
        raise NotImplementedError

