from decimal import Decimal

from mini_trading.core.enums import OrderSide, OrderStatus, OrderType
from mini_trading.core.models import AccountSnapshot, Order, Position, Symbol
from mini_trading.core.risk import RiskEngine, RiskLimits


def _order(
    *,
    order_id: str = "ord-1",
    symbol: Symbol | None = None,
    side: OrderSide = OrderSide.BUY,
    quantity: Decimal = Decimal("10"),
    status: OrderStatus = OrderStatus.CREATED,
) -> Order:
    return Order(
        order_id=order_id,
        symbol=symbol or Symbol("AAPL"),
        side=side,
        order_type=OrderType.MARKET,
        quantity=quantity,
        status=status,
    )


def _account(
    *,
    cash: Decimal = Decimal("100000"),
    position_quantity: Decimal = Decimal("0"),
) -> AccountSnapshot:
    symbol = Symbol("AAPL")
    positions = {}
    if position_quantity:
        positions[symbol] = Position(
            symbol=symbol,
            quantity=position_quantity,
            average_cost=Decimal("100"),
            last_price=Decimal("100"),
        )
    return AccountSnapshot(cash=cash, positions=positions)


def test_risk_allows_order_within_limits():
    engine = RiskEngine(
        RiskLimits(
            max_order_notional=Decimal("5000"),
            max_position_quantity=Decimal("100"),
        )
    )

    result = engine.check_order(
        _order(quantity=Decimal("10")),
        account=_account(cash=Decimal("10000")),
        reference_price=Decimal("100"),
    )

    assert result.allowed is True
    assert result.reason is None


def test_kill_switch_rejects_every_order():
    engine = RiskEngine(RiskLimits(kill_switch_enabled=True))

    result = engine.check_order(
        _order(),
        account=_account(),
        reference_price=Decimal("100"),
    )

    assert result.allowed is False
    assert result.reason == "kill switch enabled"


def test_max_order_notional_rejects_large_order():
    engine = RiskEngine(RiskLimits(max_order_notional=Decimal("999")))

    result = engine.check_order(
        _order(quantity=Decimal("10")),
        account=_account(),
        reference_price=Decimal("100"),
    )

    assert result.allowed is False
    assert result.reason == "order notional exceeds limit"


def test_cash_check_rejects_buy_order_when_cash_is_insufficient():
    engine = RiskEngine(RiskLimits())

    result = engine.check_order(
        _order(quantity=Decimal("10")),
        account=_account(cash=Decimal("999")),
        reference_price=Decimal("100"),
    )

    assert result.allowed is False
    assert result.reason == "insufficient cash"


def test_max_position_rejects_buy_order_that_would_exceed_symbol_limit():
    engine = RiskEngine(RiskLimits(max_position_quantity=Decimal("15")))

    result = engine.check_order(
        _order(quantity=Decimal("10")),
        account=_account(position_quantity=Decimal("10")),
        reference_price=Decimal("100"),
    )

    assert result.allowed is False
    assert result.reason == "position limit exceeded"


def test_sell_order_rejects_quantity_above_current_position():
    engine = RiskEngine(RiskLimits())

    result = engine.check_order(
        _order(side=OrderSide.SELL, quantity=Decimal("11")),
        account=_account(position_quantity=Decimal("10")),
        reference_price=Decimal("100"),
    )

    assert result.allowed is False
    assert result.reason == "sell quantity exceeds position"


def test_duplicate_open_order_rejects_same_symbol_and_side():
    engine = RiskEngine(RiskLimits(reject_duplicate_open_orders=True))
    open_order = _order(
        order_id="ord-open",
        status=OrderStatus.SUBMITTED,
        side=OrderSide.BUY,
    )

    result = engine.check_order(
        _order(order_id="ord-new", side=OrderSide.BUY),
        account=_account(),
        reference_price=Decimal("100"),
        open_orders=[open_order],
    )

    assert result.allowed is False
    assert result.reason == "duplicate open order"

