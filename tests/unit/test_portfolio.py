from datetime import datetime, timezone
from decimal import Decimal

import pytest

from mini_trading.core.enums import OrderSide
from mini_trading.core.models import Fill, Symbol
from mini_trading.core.portfolio import Portfolio


def _fill(
    *,
    fill_id: str = "fill-1",
    order_id: str = "ord-1",
    side: OrderSide = OrderSide.BUY,
    price: Decimal = Decimal("100"),
    quantity: Decimal = Decimal("10"),
) -> Fill:
    return Fill(
        fill_id=fill_id,
        order_id=order_id,
        symbol=Symbol("AAPL"),
        side=side,
        price=price,
        quantity=quantity,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_buy_fill_reduces_cash_and_creates_position():
    portfolio = Portfolio(cash=Decimal("100000"))

    updated = portfolio.apply_fill(_fill(price=Decimal("100"), quantity=Decimal("10")))

    position = updated.positions[Symbol("AAPL")]
    assert updated.cash == Decimal("99000")
    assert position.quantity == Decimal("10")
    assert position.average_cost == Decimal("100")
    assert position.last_price == Decimal("100")
    assert updated.realized_pnl == Decimal("0")


def test_buy_fill_updates_weighted_average_cost():
    portfolio = Portfolio(cash=Decimal("100000"))

    after_first = portfolio.apply_fill(
        _fill(fill_id="fill-1", price=Decimal("100"), quantity=Decimal("10"))
    )
    after_second = after_first.apply_fill(
        _fill(fill_id="fill-2", price=Decimal("110"), quantity=Decimal("10"))
    )

    position = after_second.positions[Symbol("AAPL")]
    assert after_second.cash == Decimal("97900")
    assert position.quantity == Decimal("20")
    assert position.average_cost == Decimal("105")


def test_sell_fill_increases_cash_reduces_position_and_realizes_pnl():
    portfolio = Portfolio(cash=Decimal("100000"))
    after_buy = portfolio.apply_fill(
        _fill(fill_id="fill-1", price=Decimal("100"), quantity=Decimal("10"))
    )

    after_sell = after_buy.apply_fill(
        _fill(
            fill_id="fill-2",
            side=OrderSide.SELL,
            price=Decimal("120"),
            quantity=Decimal("4"),
        )
    )

    position = after_sell.positions[Symbol("AAPL")]
    assert after_sell.cash == Decimal("99480")
    assert position.quantity == Decimal("6")
    assert position.average_cost == Decimal("100")
    assert position.last_price == Decimal("120")
    assert after_sell.realized_pnl == Decimal("80")


def test_sell_fill_rejects_oversell_in_long_only_mvp():
    portfolio = Portfolio(cash=Decimal("100000"))

    with pytest.raises(ValueError, match="exceeds position"):
        portfolio.apply_fill(
            _fill(side=OrderSide.SELL, price=Decimal("120"), quantity=Decimal("1"))
        )


def test_mark_price_updates_unrealized_pnl_without_changing_cash():
    portfolio = Portfolio(cash=Decimal("100000")).apply_fill(
        _fill(price=Decimal("100"), quantity=Decimal("10"))
    )

    marked = portfolio.mark_price(Symbol("AAPL"), Decimal("105"))
    snapshot = marked.snapshot()

    assert marked.cash == Decimal("99000")
    assert snapshot.pnl.realized == Decimal("0")
    assert snapshot.pnl.unrealized == Decimal("50")
    assert snapshot.equity == Decimal("100050")


def test_snapshot_combines_cash_positions_and_total_pnl():
    portfolio = Portfolio(cash=Decimal("100000"))
    after_buy = portfolio.apply_fill(
        _fill(fill_id="fill-1", price=Decimal("100"), quantity=Decimal("10"))
    )
    after_sell = after_buy.apply_fill(
        _fill(
            fill_id="fill-2",
            side=OrderSide.SELL,
            price=Decimal("120"),
            quantity=Decimal("5"),
        )
    )
    marked = after_sell.mark_price(Symbol("AAPL"), Decimal("110"))

    snapshot = marked.snapshot()

    assert snapshot.cash == Decimal("99600")
    assert snapshot.gross_market_value == Decimal("550")
    assert snapshot.pnl.realized == Decimal("100")
    assert snapshot.pnl.unrealized == Decimal("50")
    assert snapshot.pnl.total == Decimal("150")
    assert snapshot.equity == Decimal("100150")

