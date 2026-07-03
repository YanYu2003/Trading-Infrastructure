# Phase 7 Async Market Data Prototype Design

## Goal

Add an asynchronous market-data prototype without connecting to a real provider.

## Scope

Phase 7 introduces `AsyncMarketDataProvider`, `AsyncMockMarketDataProvider`, and `AsyncTradingEngine`. The async engine mirrors the synchronous demo behavior while consuming an async event stream.

## Boundary

```text
AsyncMarketDataProvider -> AsyncTradingEngine -> existing Strategy / OMS / Portfolio
```

## Out Of Scope

- real WebSocket provider
- reconnect/backoff implementation
- external market data credentials
- message queues

## Testing

Async tests verify the async engine matches the deterministic sync demo summary and that the async provider is re-iterable.
