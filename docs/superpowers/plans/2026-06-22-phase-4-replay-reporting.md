# Phase 4 Replay Reporting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add replay reporting that converts a deterministic trading run into orders, fills, account snapshots, and JSON/CSV artifacts.

**Architecture:** Phase 4 keeps reporting separate from trading logic. `TradingEngine` will record account snapshots after each event, `reports` will serialize run summaries into dictionaries/JSON/CSV, and the CLI demo will optionally write artifacts. No database is introduced in this phase.

**Tech Stack:** Python dataclasses, standard-library `json`, `csv`, `pathlib`, pytest.

---

### Task 1: Account Snapshot Recording

**Files:**
- Modify: `src/mini_trading/core/engine.py`
- Test: `tests/integration/test_event_driven_flow.py`

- [ ] **Step 1: Write failing tests**

Add assertions that `TradingRunSummary` contains an account snapshot after each processed market data event.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/integration/test_event_driven_flow.py -q`

Expected: failure because `account_snapshots` does not exist yet.

- [ ] **Step 3: Implement snapshot recording**

Extend `TradingRunSummary` with `account_snapshots` and append `OrderManager.portfolio.snapshot()` after each event.

- [ ] **Step 4: Run tests and verify pass**

Run: `python -m pytest tests/integration/test_event_driven_flow.py -q`

Expected: event flow tests pass.

### Task 2: Report Serialization

**Files:**
- Create: `src/mini_trading/reports/__init__.py`
- Create: `src/mini_trading/reports/replay.py`
- Test: `tests/unit/test_replay_report.py`

- [ ] **Step 1: Write failing tests**

Add tests for converting a `TradingRunSummary` to a report dictionary, JSON string, and CSV strings for orders, fills, and account snapshots.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/unit/test_replay_report.py -q`

Expected: failure because report modules do not exist.

- [ ] **Step 3: Implement report serialization**

Create `ReplayReport` with `from_summary()`, `to_dict()`, `to_json()`, `orders_csv()`, `fills_csv()`, and `account_snapshots_csv()`.

- [ ] **Step 4: Run tests and verify pass**

Run: `python -m pytest tests/unit/test_replay_report.py -q`

Expected: report tests pass.

### Task 3: Artifact Writer And CLI Demo

**Files:**
- Modify: `src/mini_trading/app/cli_demo.py`
- Test: `tests/integration/test_cli_demo.py`

- [ ] **Step 1: Write failing tests**

Add tests that `write_demo_reports(output_dir)` writes JSON and CSV files.

- [ ] **Step 2: Run tests and verify failure**

Run: `python -m pytest tests/integration/test_cli_demo.py -q`

Expected: failure because writer function does not exist.

- [ ] **Step 3: Implement artifact writer**

Add `write_demo_reports(output_dir)` and extend `main()` to accept optional output directory argument.

- [ ] **Step 4: Run tests and verify pass**

Run: `python -m pytest tests/integration/test_cli_demo.py -q`

Expected: CLI demo tests pass.

### Task 4: Documentation And Verification

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/resume-and-interview-notes.md`
- Modify: `docs/resume-and-interview-notes.zh.md`

- [ ] **Step 1: Update docs**

Record Phase 4 reporting behavior, replay/report concepts, demo commands, and upgraded resume bullets in English and Chinese notes.

- [ ] **Step 2: Run full verification**

Run: `python -m pytest -q`

Expected: all tests pass.

- [ ] **Step 3: Confirm local Python version**

Run: `python --version`

Expected: report the actual local version if it remains below target Python 3.11.

