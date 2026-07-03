# Phase 8 Paper Adapter Boundary Design

## Goal

Add a safe paper broker adapter boundary without implementing live or paper network submission.

## Scope

The adapter is disabled by default, requires credentials when enabled, and refuses live trading.

## Boundary

```text
OrderManager -> BrokerAdapter protocol -> PaperBrokerAdapter safety boundary
```

## Out Of Scope

- live trading
- real Alpaca/IBKR network calls
- storing credentials
- submitting orders to external systems
