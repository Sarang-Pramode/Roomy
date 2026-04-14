# Roomy — Architecture

## Packages

- **`roomy` (Python)**: instrumentation (`TraceManager`, LangChain callbacks), SQLite persistence, CLI, FastAPI read API, diagnostics, redaction, optional config file.
- **`apps/web`**: Vite + React + TypeScript + Tailwind + shadcn — consumes the read API only.
- **`agents/`**: example LangChain programs for manual testing; not shipped on PyPI.

## Data flow

1. Application calls `instrument_langchain(...)` and passes returned `callbacks` into LangChain `invoke` / `ainvoke` config (or uses `wrap_agent`).
2. Callbacks enqueue writes to SQLite (background thread + `flush()` at session end).
3. FastAPI serves read-only queries over the same SQLite file.
4. React UI lists sessions and drills into steps, segments, and findings.

## Failure modes

- Trace writes are **best-effort**: exceptions are logged and must not propagate to user agent code.
- Segment extraction failures set `reconciliation_status` on `llm_calls` and skip segment rows for that call.

## Extension points

- **Segment types**: extend `ContextSegmentType` and mapping in `segments/extractor.py`.
- **Providers**: enrich `instrumentation/serialize.py` token parsing; adjust `tokens/estimator.py` cost heuristics.
- **Storage**: replace `SqliteStore` with another backend implementing the same repository operations (future).

## Schema evolution

- SQLite `PRAGMA user_version` drives migrations in `storage/migrations.py`. Bump version when altering DDL.
