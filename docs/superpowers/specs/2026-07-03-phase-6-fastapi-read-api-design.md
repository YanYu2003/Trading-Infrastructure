# Phase 6 FastAPI Read API Design

## Goal

Expose persisted SQLite run history through read-only FastAPI endpoints.

## Scope

Phase 6 wraps the existing `SQLiteRunStore` read model. It does not submit orders, run strategies, execute broker requests, or mutate account state.

## API Boundary

```text
SQLite database -> SQLiteRunStore -> FastAPI read-only endpoints
```

## Endpoints

- `GET /health`
- `GET /runs`
- `GET /runs/{run_id}`
- `GET /runs/{run_id}/orders`
- `GET /runs/{run_id}/fills`
- `GET /runs/{run_id}/snapshots`
- `GET /runs/{run_id}/positions`
- `GET /runs/{run_id}/positions?snapshot_index=2`

## Error Handling

Missing run IDs return HTTP 404 with a clear message. Invalid route parameters are handled by FastAPI.

## Testing

Use FastAPI `TestClient` against a deterministic SQLite database created by `write_demo_sqlite()`.

## Out Of Scope

- live trading
- write endpoints
- authentication
- dashboard UI
- production deployment
