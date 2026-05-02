from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from roomy.api.upstream import list_upstream_context_steps
from roomy.diagnostics.diff import diff_llm_segments
from roomy.diagnostics.rules import export_session_markdown
from roomy.storage.sqlite_store import SqliteStore


def create_app(db_path: str) -> FastAPI:
    if not Path(db_path).exists():
        Path(db_path).touch()
    store = SqliteStore(db_path)
    app = FastAPI(title="Roomy API", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/sessions")
    def list_sessions() -> list[dict[str, Any]]:
        rows = store.query_all(
            """
            SELECT s.*,
              (SELECT SUM(COALESCE(lc.input_tokens_reported, lc.input_tokens_estimated, 0) + COALESCE(lc.output_tokens_reported, lc.output_tokens_estimated, 0))
               FROM llm_calls lc JOIN steps st ON st.step_id = lc.step_id WHERE st.session_id = s.session_id) AS total_tokens,
              (SELECT SUM(COALESCE(lc.cost_estimate_usd, 0)) FROM llm_calls lc JOIN steps st ON st.step_id = lc.step_id WHERE st.session_id = s.session_id) AS total_cost
            FROM sessions s
            ORDER BY s.started_at DESC
            LIMIT 200
            """
        )
        return [dict(r) for r in rows]

    @app.get("/sessions/{session_id}")
    def get_session(session_id: str) -> dict[str, Any]:
        row = store.query_one("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        if not row:
            raise HTTPException(404, "session not found")
        return dict(row)

    @app.get("/sessions/{session_id}/steps")
    def list_steps(session_id: str) -> list[dict[str, Any]]:
        rows = store.query_all(
            "SELECT * FROM steps WHERE session_id = ? ORDER BY step_index",
            (session_id,),
        )
        return [dict(r) for r in rows]

    @app.get("/steps/{step_id}")
    def get_step(step_id: str) -> dict[str, Any]:
        row = store.query_one("SELECT * FROM steps WHERE step_id = ?", (step_id,))
        if not row:
            raise HTTPException(404, "step not found")
        out = dict(row)
        llm = store.query_one("SELECT * FROM llm_calls WHERE step_id = ?", (step_id,))
        if llm:
            out["llm_call"] = dict(llm)
        tools = store.query_all("SELECT * FROM tool_calls WHERE step_id = ?", (step_id,))
        if tools:
            out["tool_calls"] = [dict(t) for t in tools]
        retr = store.query_all("SELECT * FROM retrieval_events WHERE step_id = ?", (step_id,))
        if retr:
            out["retrieval_events"] = [dict(t) for t in retr]
        return out

    @app.get("/steps/{step_id}/raw")
    def step_raw(step_id: str) -> JSONResponse:
        llm = store.query_one("SELECT * FROM llm_calls WHERE step_id = ?", (step_id,))
        if not llm:
            raise HTTPException(404, "no llm_call for step")
        payload = {
            "request": store.loads(llm["request_payload_json"]),
            "response": store.loads(llm["response_payload_json"]),
        }
        return JSONResponse(content=payload)

    def _segments_for_step(step_id: str) -> list[dict[str, Any]]:
        llm = store.query_one("SELECT llm_call_id FROM llm_calls WHERE step_id = ?", (step_id,))
        if not llm:
            return []
        rows = store.query_all(
            "SELECT * FROM context_segments WHERE llm_call_id = ? ORDER BY order_index",
            (llm["llm_call_id"],),
        )
        return [dict(r) for r in rows]

    @app.get("/steps/{step_id}/segments")
    def step_segments(step_id: str) -> list[dict[str, Any]]:
        return _segments_for_step(step_id)

    @app.get("/steps/{step_id}/upstream")
    def step_upstream(step_id: str) -> list[dict[str, Any]]:
        """Tool/retrieval/memory steps since the previous LLM step (heuristic context sources)."""
        rows = list_upstream_context_steps(store, step_id)
        if rows is None:
            raise HTTPException(404, "step not found")
        return rows

    @app.get("/sessions/{session_id}/findings")
    def session_findings(session_id: str) -> list[dict[str, Any]]:
        rows = store.query_all(
            "SELECT * FROM findings WHERE session_id = ? ORDER BY severity DESC",
            (session_id,),
        )
        return [dict(r) for r in rows]

    @app.get("/sessions/{session_id}/export.json")
    def export_json(session_id: str) -> JSONResponse:
        s = store.query_one("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
        if not s:
            raise HTTPException(404, "session not found")
        steps = store.query_all("SELECT * FROM steps WHERE session_id = ? ORDER BY step_index", (session_id,))
        findings = store.query_all("SELECT * FROM findings WHERE session_id = ?", (session_id,))
        payload = {
            "session": dict(s),
            "steps": [dict(x) for x in steps],
            "findings": [dict(x) for x in findings],
        }
        return JSONResponse(content=json.loads(json.dumps(payload, default=str)))

    @app.get("/sessions/{session_id}/export.md", response_class=PlainTextResponse)
    def export_md(session_id: str) -> str:
        return export_session_markdown(store, session_id)

    @app.get("/sessions/{session_id}/diff")
    def session_diff(session_id: str, a: str, b: str) -> dict[str, Any]:
        """Diff segments between two steps (query params: a=step_id, b=step_id)."""
        for sid in (a, b):
            row = store.query_one("SELECT session_id FROM steps WHERE step_id = ?", (sid,))
            if not row or row["session_id"] != session_id:
                raise HTTPException(400, "steps must belong to session")
        sa = _segments_for_step(a)
        sb = _segments_for_step(b)
        return diff_llm_segments(sa, sb)

    return app
