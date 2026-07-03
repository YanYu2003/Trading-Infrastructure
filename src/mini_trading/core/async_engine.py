from __future__ import annotations

from mini_trading.core.engine import TradingRunSummary
from mini_trading.core.enums import MarketDataEventType
from mini_trading.core.models import AccountSnapshot, Fill, Trade
from mini_trading.core.oms import OrderManager, OrderSubmissionResult
from mini_trading.marketdata.async_base import AsyncMarketDataProvider
from mini_trading.strategies.base import Strategy, StrategySignal


class AsyncTradingEngine:
    def __init__(
        self,
        *,
        market_data: AsyncMarketDataProvider,
        strategy: Strategy,
        order_manager: OrderManager,
    ) -> None:
        self._market_data = market_data
        self._strategy = strategy
        self._order_manager = order_manager

    async def run(self) -> TradingRunSummary:
        events_processed = 0
        signals: list[StrategySignal] = []
        order_results: list[OrderSubmissionResult] = []
        fills: list[Fill] = []
        account_snapshots: list[AccountSnapshot] = []

        async for event in self._market_data.stream():
            events_processed += 1
            if (
                event.event_type is MarketDataEventType.TRADE
                and isinstance(event.payload, Trade)
            ):
                self._order_manager.portfolio = (
                    self._order_manager.portfolio.mark_price(
                        event.symbol, event.payload.price
                    )
                )
            signal = self._strategy.on_event(event)
            if signal is None:
                account_snapshots.append(self._order_manager.portfolio.snapshot())
                continue

            signals.append(signal)
            result = self._order_manager.submit_order(
                symbol=signal.symbol,
                side=signal.side,
                order_type=signal.order_type,
                quantity=signal.quantity,
                market_price=signal.reference_price,
            )
            order_results.append(result)
            fills.extend(result.fills)
            on_order_result = getattr(self._strategy, "on_order_result", None)
            if on_order_result is not None:
                on_order_result(result)
            account_snapshots.append(self._order_manager.portfolio.snapshot())

        return TradingRunSummary(
            events_processed=events_processed,
            signals=signals,
            order_results=order_results,
            fills=fills,
            account=self._order_manager.portfolio.snapshot(),
            account_snapshots=account_snapshots,
        )
