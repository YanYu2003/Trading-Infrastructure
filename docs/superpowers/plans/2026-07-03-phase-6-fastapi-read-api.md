# Phase 6 FastAPI Read API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add read-only FastAPI endpoints for SQLite run history.

**Architecture:** FastAPI depends on `SQLiteRunStore`; trading core modules remain independent from HTTP and persistence.

**Tech Stack:** FastAPI, Uvicorn, FastAPI TestClient, pytest, SQLite.

---

### Task 1: API Tests

**Files:**
- Create: `tests/integration/test_read_api.py`

- [x] **Step 1: Write failing tests**

Tests cover `/health`, `/runs`, run detail, orders, fills, snapshots, positions, and missing run 404.

- [x] **Step 2: Verify red**

Observed missing FastAPI/API module failures before implementation.

### Task 2: API Implementation

**Files:**
- Create: `src/mini_trading/app/api.py`
- Modify: `pyproject.toml`

- [x] **Step 1: Add dependencies**

Added FastAPI/Uvicorn runtime dependencies and `httpx` test dependency.

- [x] **Step 2: Implement read-only API**

Implemented `create_app(db_path)` and module-level `app`.

- [x] **Step 3: Verify**

`tests/integration/test_read_api.py` passes.

### Task 3: Full Verification

- [x] **Step 1: Run full test suite**

`86 passed`.
