from datetime import datetime, timezone
from decimal import Decimal

from mini_trading.brokers.base import BrokerResult
from mini_trading.core.enums import MarketDataEventType, OrderSide, OrderStatus, OrderType
from mini_trading.core.models import Fill, MarketDataEvent, Order, Quote, Symbol, Trade
from mini_trading.core.oms import OrderSubmissionResult
from mini_trading.core.risk import RiskCheckResult
from mini_trading.strategies.threshold import PriceThresholdStrategy


def _trade_event(price: Decimal) -> MarketDataEvent:
    trade = Trade(
        symbol=Symbol("AAPL"),
        price=price,
        quantity=Decimal("10"),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    return MarketDataEvent(
        event_type=MarketDataEventType.TRADE,
        payload=trade,
        received_at=trade.timestamp,
    )


def _order_result(
    *,
    side: OrderSide = OrderSide.BUY,
    status: OrderStatus = OrderStatus.FILLED,
    fill_quantity: Decimal = Decimal("10"),
) -> OrderSubmissionResult:
    order = Order(
        order_id="ord-1",
        symbol=Symbol("AAPL"),
        side=side,
        order_type=OrderType.MARKET,
        quantity=Decimal("10"),
        status=status,
        filled_quantity=fill_quantity if status is not OrderStatus.REJECTED else Decimal("0"),
    )
    fills = []
    if fill_quantity:
        fills.append(
            Fill(
                fill_id="fill-1",
                order_id=order.order_id,
                symbol=order.symbol,
                side=side,
                price=Decimal("99"),
                quantity=fill_quantity,
                timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        )
    return OrderSubmissionResult(
        order=order,
        risk_result=RiskCheckResult.allow(),
        broker_result=BrokerResult(status=status, fills=fills),
        fills=fills,
    )


def test_strategy_emits_buy_signal_below_buy_threshold():
    strategy = PriceThresholdStrategy(
        symbol=Symbol("AAPL"),
        buy_below=Decimal("100"),
        sell_above=Decimal("110"),
        quantity=Decimal("10"),
    )

    signal = strategy.on_event(_trade_event(Decimal("99")))

    assert signal is not None
    assert signal.symbol == Symbol("AAPL")
    assert signal.side is OrderSide.BUY
    assert signal.order_type is OrderType.MARKET
    assert signal.quantity == Decimal("10")
    assert signal.reference_price == Decimal("99")


def test_strategy_emits_sell_signal_above_sell_threshold_after_buy():
    strategy = PriceThresholdStrategy(
        symbol=Symbol("AAPL"),
        buy_below=Decimal("100"),
        sell_above=Decimal("110"),
        quantity=Decimal("10"),
    )

    strategy.on_event(_trade_event(Decimal("99")))
    strategy.on_order_result(_order_result(side=OrderSide.BUY))
    signal = strategy.on_event(_trade_event(Decimal("111")))

    assert signal is not None
    assert signal.side is OrderSide.SELL
    assert signal.reference_price == Decimal("111")


def test_strategy_emits_no_signal_inside_threshold_band():
    strategy = PriceThresholdStrategy(
        symbol=Symbol("AAPL"),
        buy_below=Decimal("100"),
        sell_above=Decimal("110"),
        quantity=Decimal("10"),
    )

    assert strategy.on_event(_trade_event(Decimal("105"))) is None


def test_strategy_ignores_quote_events():
    quote = Quote(
        symbol=Symbol("AAPL"),
        bid=Decimal("99"),
        ask=Decimal("99.05"),
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    event = MarketDataEvent(
        event_type=MarketDataEventType.QUOTE,
        payload=quote,
        received_at=quote.timestamp,
    )
    strategy = PriceThresholdStrategy(
        symbol=Symbol("AAPL"),
        buy_below=Decimal("100"),
        sell_above=Decimal("110"),
        quantity=Decimal("10"),
    )

    assert strategy.on_event(event) is None


def test_strategy_does_not_emit_duplicate_buy_while_position_is_open():
    strategy = PriceThresholdStrategy(
        symbol=Symbol("AAPL"),
        buy_below=Decimal("100"),
        sell_above=Decimal("110"),
        quantity=Decimal("10"),
    )

    first = strategy.on_event(_trade_event(Decimal("99")))
    second = strategy.on_event(_trade_event(Decimal("98")))

    assert first is not None
    assert second is None


def test_strategy_recovers_from_rejected_buy_signal():
    strategy = PriceThresholdStrategy(
        symbol=Symbol("AAPL"),
        buy_below=Decimal("100"),
        sell_above=Decimal("110"),
        quantity=Decimal("10"),
    )

    first = strategy.on_event(_trade_event(Decimal("99")))
    strategy.on_order_result(
        _order_result(status=OrderStatus.REJECTED, fill_quantity=Decimal("0"))
    )
    second = strategy.on_event(_trade_event(Decimal("98")))

    assert first is not None
    assert second is not None
