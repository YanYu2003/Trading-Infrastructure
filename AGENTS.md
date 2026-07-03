# AGENTS.md

## Project Mission

Build a resume-ready US equity mini trading infrastructure project that demonstrates real-time market data handling, Mini OMS design, pre-trade risk checks, mock execution, and account/PnL updates.

This project is an engineering demonstration. It is not investment advice and must not guide real-money trading.

## Safety Rules

- Default all trading behavior to mock or paper trading.
- Keep `ENABLE_LIVE_TRADING=false` as the default safety stance.
- Do not add live trading support in the MVP.
- Do not commit API keys, tokens, passwords, private keys, account IDs, or broker credentials.
- Any future feature that approaches live trading must be explicitly disabled by default and documented in code and README.
- Prefer deterministic mock data for tests and demos.

## Development Rules

- Use Python 3.11 or 3.12 in a project-local `.venv`.
- Keep domain logic under `src/mini_trading/core`.
- Keep broker integrations behind adapter interfaces under `src/mini_trading/brokers`.
- Keep market data integrations behind provider interfaces under `src/mini_trading/marketdata`.
- Keep strategies as signal generators. Strategies must not directly mutate orders, cash, positions, or PnL.
- Add tests for core behavior before implementing production logic.
- Run `python -m pytest -q` before claiming a phase is complete.
- Prefer small, reviewable increments over large rewrites.

## Commit Guidance

- Use concise commit messages such as `docs: add architecture overview` or `test: add order state smoke test`.
- Do not mix unrelated changes in the same commit.
- Do not rewrite user changes unless explicitly requested.

