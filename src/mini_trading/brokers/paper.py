from __future__ import annotations

import os
from dataclasses import dataclass
from decimal import Decimal

from mini_trading.brokers.base import BrokerResult
from mini_trading.core.models import Order


class PaperTradingDisabled(RuntimeError):
    pass


class PaperTradingNotImplemented(NotImplementedError):
    pass


@dataclass(frozen=True)
class PaperBrokerSettings:
    enabled: bool = False
    api_key: str | None = None
    api_secret: str | None = None
    endpoint: str = "https://paper-api.example.test"
    live_trading_enabled: bool = False

    @classmethod
    def from_env(cls) -> "PaperBrokerSettings":
        return cls(
            enabled=_env_bool("ENABLE_PAPER_TRADING"),
            api_key=os.getenv("PAPER_BROKER_API_KEY"),
            api_secret=os.getenv("PAPER_BROKER_API_SECRET"),
            endpoint=os.getenv(
                "PAPER_BROKER_ENDPOINT",
                "https://paper-api.example.test",
            ),
            live_trading_enabled=_env_bool("ENABLE_LIVE_TRADING"),
        )

    def __post_init__(self) -> None:
        if self.live_trading_enabled:
            raise ValueError("live trading must remain disabled")


class PaperBrokerAdapter:
    def __init__(self, *, settings: PaperBrokerSettings | None = None) -> None:
        self._settings = settings or PaperBrokerSettings()
        if self._settings.enabled and (
            not self._settings.api_key or not self._settings.api_secret
        ):
            raise ValueError("api_key and api_secret are required for paper trading")

    @property
    def settings(self) -> PaperBrokerSettings:
        return self._settings

    def submit_order(self, order: Order, *, market_price: Decimal) -> BrokerResult:
        if not self._settings.enabled:
            raise PaperTradingDisabled("paper trading is disabled")
        raise PaperTradingNotImplemented(
            "paper broker network submission is not implemented"
        )


def _env_bool(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}
