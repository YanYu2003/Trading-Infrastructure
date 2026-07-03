from decimal import Decimal

from mini_trading.brokers.mock import MockBroker
from mini_trading.core.enums import OrderSide, OrderStatus, OrderType
from mini_trading.core.models import Symbol
from mini_trading.core.oms import OrderManager
from mini_trading.core.portfolio import Portfolio
from mini_trading.core.risk import RiskEngine, RiskLimits


def test_buy_then_sell_flow_updates_orders_cash_position_and_pnl():
    manager = OrderManager(
        portfolio=Portfolio(cash=Decimal("100000")),
        risk_engine=RiskEngine(
            RiskLimits(
                max_order_notional=Decimal("10000"),
                max_position_quantity=Decimal("100"),
            )
        ),
        broker=MockBroker(),
    )

    buy = manager.submit_order(
        symbol=Symbol("AAPL"),
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        market_price=Decimal("100"),
    )
    sell = manager.submit_order(
        symbol=Symbol("AAPL"),
        side=OrderSide.SELL,
        order_type=OrderType.MARKET,
        quantity=Decimal("4"),
        market_price=Decimal("120"),
    )
    snapshot = manager.portfolio.mark_price(Symbol("AAPL"), Decimal("110")).snapshot()

    assert buy.order.status is OrderStatus.FILLED
    assert sell.order.status is OrderStatus.FILLED
    assert len(manager.orders) == 2
    assert len(manager.fills) == 2
    assert snapshot.cash == Decimal("99480")
    assert snapshot.positions[Symbol("AAPL")].quantity == Decimal("6")
    assert snapshot.pnl.realized == Decimal("80")
    assert snapshot.pnl.unrealized == Decimal("60")
    assert snapshot.equity == Decimal("100140")

