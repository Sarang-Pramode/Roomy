# Roomy — status & roadmap checklist

This document aligns the repo with the **Roomy observability MVP** Cursor plan (`roomy_observability_mvp_68656ab5.plan.md`, typically under `~/.cursor/plans/`) and the original product goals: **local-first LangChain observability**, **minimal integration**, **structured traces**, **context decomposition**, **inspectable runs** (CLI + UI), then **diagnostics** and **depth** (RAG / tools / memory).

**Distribution:** PyPI `roomy-observability` · **Import:** `roomy` · **Repo:** [github.com/Sarang-Pramode/Roomy](https://github.com/Sarang-Pramode/Roomy)

---

## Completed (shipped in tree today)

### Phase 0 — Capture foundation
- [x] Trace schema in SQLite (`sessions`, `steps`, `llm_calls`, `tool_calls`, `retrieval_events`, `context_segments`, `findings`) + versioned migrations
- [x] `TraceManager` + LangChain **sync/async** callbacks (LLM, tool, retriever, chain/control for parent linkage)
- [x] Best-effort persistence (errors must not break agents); background write queue + `flush()`
- [x] Typer CLI: `sessions list` / `show`, `step-dump`, `tokens`, `serve`
- [x] Public API: `instrument_langchain`, `RoomyBindings`, `wrap_agent`, `end_session`

### Phase 1 — Context decomposition
- [x] Context segments from messages + token estimates (tiktoken optional)
- [x] Per–LLM-call segment summary JSON; `reconciliation_status` on LLM rows

### Phase 2 — Local web UI
- [x] FastAPI read API (sessions, steps, segments, raw, findings, export, diff helper)
- [x] Vite + React + TS + Tailwind + shadcn-style UI: sessions, timeline, step detail, composition bar, raw tab

### Phase 3 — Diagnostics
- [x] Segment diff helper + API route
- [x] Deterministic findings (oversized tool output, repeated segments, history-heavy context, cumulative token warning)
- [x] Findings in UI; session export JSON / Markdown

### Phase 4–5 — Partial (foundation only)
- [x] Retrieval + tool events captured when LangChain emits those callbacks
- [x] Redaction pipeline + YAML config loading (`ROOMY_CONFIG`)
- [x] `parent_step_id` / control steps for nested runs (basic)
- [x] Docker Compose + Dockerfile for API
- [x] **PyPI:** `roomy-observability` published; **Trusted Publishing** via GitHub Actions (`publish-pypi.yml`, `release` environment)
- [x] Docs: DESIGN, ARCHITECTURE, DEVELOPMENT; Cursor rules; `agents/` samples (`minimal_chain`, `minimal_tools`)
- [x] Smoke tests + ruff config

---

## Partially done (needs more work to match spec intent)

- [ ] **Phase 4 — Correlation UX:** Link “this retrieval / tool output **fed** this LLM step” explicitly in the UI (beyond listing rows on a step).
- [ ] **Phase 4 — Memory:** First-class capture/UI for memory reads/writes (schema hooks exist; product depth does not).
- [ ] **Phase 3 — Diff in UI:** Step-to-step diff surfaced as a dedicated view (API exists; UI is minimal).
- [ ] **Phase 2 — Charts:** Treemap / richer composition viz (stacked bar is minimal).
- [ ] **Packaged UI:** Prebuilt static assets in wheel or single-command “UI + API” story (today: `roomy serve` + separate `apps/web` dev build).
- [ ] **Test & types:** Broad pytest coverage; stricter mypy on public APIs.
- [ ] **LangGraph / multi-agent:** Battle-tested patterns beyond core callbacks.

---

## Planned (recommended next slices)

Ordered roughly by leverage:

1. **Correlation panel (Phase 4)** — Graph or table: retrieval/tool steps → consuming LLM step(s); optional “inserted vs returned” doc counts.
2. **Step diff UI (Phase 3)** — Pick two steps; show segment/token delta in the browser.
3. **More agents (Phase 0–4)** — LangGraph + RAG example under `agents/` to stress-test capture.
4. **Memory events (Phase 4)** — `memory` step type events + UI filter.
5. **Redaction presets (Phase 5)** — Config profiles; optional “no full text” mode documented end-to-end.
6. **Hardening (Phase 5)** — Fuzzier LangChain versions; concurrency stress; migration tests.

---

## End state (north star)

What “done enough” looks like for the **MVP** described in the plan:

| Goal | Target |
|------|--------|
| Integration | Instrument a custom LangChain agent in **~15 minutes** with callbacks (or wrapper). |
| Visibility | Every **LLM call** in a session captured with **input/output**, **tokens**, **latency**. |
| Context | Each call has **labeled segments** + estimates; **reported vs estimated** tokens distinguished. |
| Inspection | **CLI + local web UI** to browse sessions, timeline, step detail, raw payloads. |
| Diagnostics | Tooling flags **obvious waste** (bloated tool output, repetition, history-heavy context, overflow risk). |
| Safety | Trace failures **never crash** the agent; sensitive fields **redactable**. |
| Distribution | **Installable from PyPI** (`roomy-observability`); **releases** reproducible from GitHub. |

**Post-MVP (v1.x+):** Deeper RAG/memory story, nested/sub-agent ergonomics, optional hosted mode, broader framework adapters—only if you expand scope beyond “LangChain-first local tool.”

---

## How to re-read the original plan

The Cursor plan file usually lives outside this git repo, e.g.  
`~/.cursor/plans/roomy_observability_mvp_68656ab5.plan.md`.

This `STATUS.md` is the **in-repo** checklist you can commit and update each release.

---

*Last reviewed: align with repo `main` and PyPI automation in place.*
