from mini_trading import __version__
from mini_trading.config import DEFAULT_TRADING_MODE, LIVE_TRADING_ENABLED


def test_package_imports_with_safe_defaults():
    assert __version__ == "0.1.0"
    assert DEFAULT_TRADING_MODE == "mock"
    assert LIVE_TRADING_ENABLED is False

