# Phase 7 Async Market Data Prototype Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic async market-data prototype.

**Architecture:** Async provider feeds an async engine; strategy, OMS, broker, and portfolio stay synchronous and reusable.

**Tech Stack:** Python `asyncio`, async iterators, pytest-asyncio.

---

### Task 1: Async Tests

- [x] Add async integration tests for deterministic summary and provider re-iterability.
- [x] Verify tests fail before implementation.

### Task 2: Async Implementation

- [x] Add `AsyncMarketDataProvider` protocol.
- [x] Add `AsyncMockMarketDataProvider`.
- [x] Add `AsyncTradingEngine`.
- [x] Add `pytest-asyncio` dev dependency.
- [x] Verify phase tests and full suite.
