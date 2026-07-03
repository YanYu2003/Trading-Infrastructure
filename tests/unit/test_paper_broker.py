from decimal import Decimal

import pytest

from mini_trading.brokers.paper import (
    PaperBrokerAdapter,
    PaperBrokerSettings,
    PaperTradingDisabled,
    PaperTradingNotImplemented,
)
from mini_trading.core.enums import OrderSide, OrderType
from mini_trading.core.models import Order, Symbol


def _order() -> Order:
    return Order(
        order_id="paper-1",
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("1"),
    )


def test_paper_broker_is_disabled_by_default():
    settings = PaperBrokerSettings()
    broker = PaperBrokerAdapter(settings=settings)

    with pytest.raises(PaperTradingDisabled, match="paper trading is disabled"):
        broker.submit_order(_order(), market_price=Decimal("100"))


def test_paper_broker_requires_credentials_when_enabled():
    settings = PaperBrokerSettings(enabled=True)

    with pytest.raises(ValueError, match="api_key and api_secret are required"):
        PaperBrokerAdapter(settings=settings)


def test_paper_broker_enabled_boundary_does_not_implement_network_call():
    settings = PaperBrokerSettings(
        enabled=True,
        api_key="paper-key",
        api_secret="paper-secret",
        endpoint="https://paper-api.example.test",
    )
    broker = PaperBrokerAdapter(settings=settings)

    with pytest.raises(PaperTradingNotImplemented, match="not implemented"):
        broker.submit_order(_order(), market_price=Decimal("100"))


def test_paper_settings_from_env_keeps_live_trading_disabled(monkeypatch):
    monkeypatch.setenv("ENABLE_PAPER_TRADING", "true")
    monkeypatch.setenv("PAPER_BROKER_API_KEY", "paper-key")
    monkeypatch.setenv("PAPER_BROKER_API_SECRET", "paper-secret")
    monkeypatch.setenv("PAPER_BROKER_ENDPOINT", "https://paper-api.example.test")

    settings = PaperBrokerSettings.from_env()

    assert settings.enabled is True
    assert settings.live_trading_enabled is False
    assert settings.endpoint == "https://paper-api.example.test"
