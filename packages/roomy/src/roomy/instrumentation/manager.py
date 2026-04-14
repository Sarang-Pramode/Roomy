from __future__ import annotations

import logging
import queue
import threading
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any

from langchain_core.outputs import LLMResult

from roomy.config.settings import RoomyConfig
from roomy.instrumentation.serialize import (
    llm_result_to_dict,
    serialized_name,
    token_usage_from_llm_result,
)
from roomy.redaction.pipeline import redact_json, redact_text
from roomy.segments.extractor import extract_segments_for_llm_call
from roomy.storage.sqlite_store import SqliteStore, _iso, _utcnow
from roomy.tokens.estimator import TokenEstimator, estimate_cost_usd

logger = logging.getLogger("roomy")


def _safe(fn: Callable[[], None]) -> None:
    try:
        fn()
    except Exception:
        logger.exception("roomy: trace write failed (suppressed)")


class TraceManager:
    """Coordinates session lifecycle, step/span mapping, and best-effort persistence."""

    def __init__(self, store: SqliteStore, config: RoomyConfig | None = None) -> None:
        self._store = store
        self._config = config or RoomyConfig()
        self._session_id: str | None = None
        self._step_index = 0
        self._run_to_step: dict[str, str] = {}
        self._pending_llm: dict[str, dict[str, Any]] = {}
        self._pending_tool: dict[str, dict[str, Any]] = {}
        self._pending_retrieval: dict[str, dict[str, Any]] = {}
        self._q: queue.Queue[Callable[[], None]] = queue.Queue()
        self._worker = threading.Thread(target=self._drain, name="roomy-writer", daemon=True)
        self._worker.start()

    def _enqueue(self, fn: Callable[[], None]) -> None:
        self._q.put(fn)

    def _drain(self) -> None:
        while True:
            fn = self._q.get()
            try:
                fn()
            except Exception:
                logger.exception("roomy: background trace write failed")
            finally:
                self._q.task_done()

    def flush(self) -> None:
        """Block until queued writes finish (best-effort)."""
        self._q.join()

    @property
    def session_id(self) -> str | None:
        return self._session_id

    def start_session(self, agent_name: str, environment: str = "dev", metadata: dict | None = None) -> str:
        sid = str(uuid.uuid4())
        self._session_id = sid
        self._step_index = 0
        self._run_to_step.clear()
        self._pending_llm.clear()
        self._pending_tool.clear()
        self._pending_retrieval.clear()
        meta = metadata or {}
        now = _utcnow()

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    """
                    INSERT INTO sessions (session_id, agent_name, environment, started_at, ended_at, status, metadata_json)
                    VALUES (?, ?, ?, ?, NULL, 'running', ?)
                    """,
                    (sid, agent_name, environment, _iso(now), self._store.dumps(meta)),
                )

        _safe(_write)
        return sid

    def end_session(self, status: str = "completed") -> None:
        if not self._session_id:
            return
        sid = self._session_id
        now = _utcnow()

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    """
                    UPDATE sessions SET ended_at = ?, status = ? WHERE session_id = ?
                    """,
                    (_iso(now), status, sid),
                )

        self._enqueue(_write)

    def chain_start(
        self,
        *,
        run_id: str | None,
        parent_run_id: str | None,
        serialized: dict[str, Any] | None,
    ) -> str | None:
        if not self._session_id or not run_id:
            return None
        sid = self._session_id
        step_id = str(uuid.uuid4())
        parent_step = self._run_to_step.get(parent_run_id) if parent_run_id else None
        name = serialized_name(serialized)
        idx = self._step_index
        self._step_index += 1
        now = _utcnow()

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    """
                    INSERT INTO steps (step_id, session_id, parent_step_id, step_index, step_type, started_at, ended_at, latency_ms, status, metadata_json)
                    VALUES (?, ?, ?, ?, 'control', ?, NULL, NULL, 'running', ?)
                    """,
                    (
                        step_id,
                        sid,
                        parent_step,
                        idx,
                        _iso(now),
                        self._store.dumps({"name": name}),
                    ),
                )

        self._enqueue(_write)
        self._run_to_step[run_id] = step_id
        return step_id

    def chain_end(self, *, run_id: str | None) -> None:
        if not run_id:
            return
        step_id = self._run_to_step.pop(run_id, None)
        if not step_id:
            return
        now = _utcnow()

        def _write() -> None:
            with self._store.write() as conn:
                row = conn.execute(
                    "SELECT started_at FROM steps WHERE step_id = ?", (step_id,)
                ).fetchone()
                started = datetime.fromisoformat(row["started_at"]) if row else now
                lat = int((now - started).total_seconds() * 1000)
                conn.execute(
                    """
                    UPDATE steps SET ended_at = ?, latency_ms = ?, status = 'completed' WHERE step_id = ?
                    """,
                    (_iso(now), lat, step_id),
                )

        self._enqueue(_write)

    def llm_start(
        self,
        *,
        run_id: str | None,
        parent_run_id: str | None,
        serialized: dict[str, Any] | None,
        prompts: Any,
        invocation_params: dict[str, Any] | None = None,
    ) -> None:
        if not self._session_id or not run_id:
            return
        sid = self._session_id
        step_id = str(uuid.uuid4())
        llm_call_id = str(uuid.uuid4())
        parent_step = self._run_to_step.get(parent_run_id) if parent_run_id else None
        idx = self._step_index
        self._step_index += 1
        now = _utcnow()
        provider = "unknown"
        model = "unknown"
        if invocation_params:
            model = str(invocation_params.get("model") or model)
            provider = str(invocation_params.get("provider") or provider)
        if serialized:
            kwargs = serialized.get("kwargs") or {}
            model = str(kwargs.get("model") or kwargs.get("model_name") or model)
        req_raw: dict[str, Any] = {
            "serialized": serialized,
            "prompts_repr": self._prompts_summary(prompts),
        }
        if self._config.capture_raw:
            req_raw["prompts"] = self._serialize_prompts(prompts)
        cfg_r = self._config.redaction or None
        if cfg_r:
            req_raw = redact_json(req_raw, cfg_r)  # type: ignore[arg-type]

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    """
                    INSERT INTO steps (step_id, session_id, parent_step_id, step_index, step_type, started_at, ended_at, latency_ms, status, metadata_json)
                    VALUES (?, ?, ?, ?, 'llm', ?, NULL, NULL, 'running', ?)
                    """,
                    (
                        step_id,
                        sid,
                        parent_step,
                        idx,
                        _iso(now),
                        self._store.dumps({"run_id": run_id, "lc_name": serialized_name(serialized)}),
                    ),
                )
                conn.execute(
                    """
                    INSERT INTO llm_calls (llm_call_id, step_id, provider, model, request_payload_json, response_payload_json,
                      input_tokens_reported, output_tokens_reported, input_tokens_estimated, output_tokens_estimated,
                      cached_tokens, cost_estimate_usd, reconciliation_status, segment_summary_json, started_at, ended_at)
                    VALUES (?, ?, ?, ?, ?, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, ?, NULL)
                    """,
                    (
                        llm_call_id,
                        step_id,
                        provider,
                        model,
                        self._store.dumps(req_raw),
                        _iso(now),
                    ),
                )

        self._enqueue(_write)
        self._run_to_step[run_id] = step_id
        self._pending_llm[run_id] = {
            "step_id": step_id,
            "llm_call_id": llm_call_id,
            "started_at": now,
            "prompts": prompts,
            "model": model,
        }

    def llm_end(self, *, run_id: str | None, result: LLMResult) -> None:
        if not run_id or run_id not in self._pending_llm:
            return
        pending = self._pending_llm.pop(run_id)
        step_id = pending["step_id"]
        llm_call_id = pending["llm_call_id"]
        started: datetime = pending["started_at"]
        prompts = pending["prompts"]
        model = str(pending["model"])
        now = _utcnow()
        lat = int((now - started).total_seconds() * 1000)
        resp = llm_result_to_dict(result)
        cfg_r = self._config.redaction or None
        if cfg_r:
            resp = redact_json(resp, cfg_r)  # type: ignore[arg-type]
        inp_r, out_r, cached = token_usage_from_llm_result(result)
        est = TokenEstimator(model_hint=model)
        prompts_for_est = self._serialize_prompts(prompts)
        inp_e = est.count_messages(prompts_for_est) if isinstance(prompts_for_est, list) else est.count(
            str(prompts_for_est)
        )
        out_text = ""
        if result.generations:
            try:
                g0 = result.generations[0][0]
                if isinstance(g0, str):
                    out_text = g0
                else:
                    out_text = str(getattr(g0, "text", None) or "")
            except Exception:
                out_text = ""
        out_e = est.count(out_text)
        cost = estimate_cost_usd(model, inp_r or inp_e or 0, out_r or out_e or 0)

        segments_sql: list[tuple] = []
        summary_json: str | None = None
        recon = "skipped"
        try:
            segs, summary = extract_segments_for_llm_call(llm_call_id, prompts, model_hint=model)
            summary_json = self._store.dumps(summary)
            store_full = bool(cfg_r.store_full_text) if cfg_r else True
            for s in segs:
                text_full = s.full_text if store_full else None
                preview = s.text_preview
                if cfg_r and preview:
                    preview = redact_text(preview, cfg_r)
                if cfg_r and text_full:
                    text_full = redact_text(text_full, cfg_r)
                segments_sql.append(
                    (
                        s.segment_id,
                        llm_call_id,
                        s.order_index,
                        s.segment_type.value,
                        s.source_kind,
                        s.source_name,
                        preview,
                        text_full,
                        s.token_count,
                        s.byte_count,
                        self._store.dumps(s.metadata),
                    )
                )
            recon = "ok"
        except Exception:
            logger.exception("roomy: segment extraction failed")
            recon = "error"

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    """
                    UPDATE llm_calls SET
                      response_payload_json = ?,
                      input_tokens_reported = ?,
                      output_tokens_reported = ?,
                      input_tokens_estimated = ?,
                      output_tokens_estimated = ?,
                      cached_tokens = ?,
                      cost_estimate_usd = ?,
                      reconciliation_status = ?,
                      segment_summary_json = ?,
                      ended_at = ?
                    WHERE llm_call_id = ?
                    """,
                    (
                        self._store.dumps(resp),
                        inp_r,
                        out_r,
                        inp_e,
                        out_e,
                        cached,
                        cost,
                        recon,
                        summary_json,
                        _iso(now),
                        llm_call_id,
                    ),
                )
                conn.execute(
                    """
                    UPDATE steps SET ended_at = ?, latency_ms = ?, status = 'completed' WHERE step_id = ?
                    """,
                    (_iso(now), lat, step_id),
                )
                conn.execute("DELETE FROM context_segments WHERE llm_call_id = ?", (llm_call_id,))
                for row in segments_sql:
                    conn.execute(
                        """
                        INSERT INTO context_segments (segment_id, llm_call_id, order_index, segment_type, source_kind, source_name, text_preview, full_text, token_count, byte_count, metadata_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        row,
                    )

        self._enqueue(_write)

    def llm_error(self, *, run_id: str | None) -> None:
        if not run_id or run_id not in self._pending_llm:
            return
        pending = self._pending_llm.pop(run_id)
        step_id = pending["step_id"]
        llm_call_id = pending["llm_call_id"]
        started: datetime = pending["started_at"]
        now = _utcnow()
        lat = int((now - started).total_seconds() * 1000)

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    "UPDATE steps SET ended_at = ?, latency_ms = ?, status = 'failed' WHERE step_id = ?",
                    (_iso(now), lat, step_id),
                )
                conn.execute(
                    "UPDATE llm_calls SET ended_at = ?, reconciliation_status = 'error' WHERE llm_call_id = ?",
                    (_iso(now), llm_call_id),
                )

        self._enqueue(_write)

    def tool_start(
        self,
        *,
        run_id: str | None,
        parent_run_id: str | None,
        serialized: dict[str, Any] | None,
        inputs: Any,
    ) -> None:
        if not self._session_id or not run_id:
            return
        sid = self._session_id
        step_id = str(uuid.uuid4())
        tool_call_id = str(uuid.uuid4())
        parent_step = self._run_to_step.get(parent_run_id) if parent_run_id else None
        idx = self._step_index
        self._step_index += 1
        now = _utcnow()
        name = serialized_name(serialized)
        args = inputs if isinstance(inputs, dict) else {"input": inputs}

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    """
                    INSERT INTO steps (step_id, session_id, parent_step_id, step_index, step_type, started_at, ended_at, latency_ms, status, metadata_json)
                    VALUES (?, ?, ?, ?, 'tool', ?, NULL, NULL, 'running', ?)
                    """,
                    (step_id, sid, parent_step, idx, _iso(now), self._store.dumps({"run_id": run_id})),
                )
                conn.execute(
                    """
                    INSERT INTO tool_calls (tool_call_id, step_id, tool_name, tool_args_json, tool_output_preview, output_size_bytes, latency_ms, status, metadata_json, started_at, ended_at)
                    VALUES (?, ?, ?, ?, NULL, NULL, NULL, 'running', '{}', ?, NULL)
                    """,
                    (
                        tool_call_id,
                        step_id,
                        name,
                        self._store.dumps(redact_json(args, self._config.redaction) if self._config.redaction else args),
                        _iso(now),
                    ),
                )

        self._enqueue(_write)
        self._run_to_step[run_id] = step_id
        self._pending_tool[run_id] = {"step_id": step_id, "tool_call_id": tool_call_id, "started_at": now}

    def tool_end(self, *, run_id: str | None, output: Any) -> None:
        if not run_id or run_id not in self._pending_tool:
            return
        p = self._pending_tool.pop(run_id)
        now = _utcnow()
        lat = int((now - p["started_at"]).total_seconds() * 1000)
        text = str(output) if output is not None else ""
        preview = text[:2000] + ("…" if len(text) > 2000 else "")
        cfg_r = self._config.redaction
        if cfg_r:
            preview = redact_text(preview, cfg_r)
        size = len(text.encode("utf-8"))

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    """
                    UPDATE tool_calls SET tool_output_preview = ?, output_size_bytes = ?, latency_ms = ?, status = 'completed', ended_at = ?
                    WHERE tool_call_id = ?
                    """,
                    (preview, size, lat, _iso(now), p["tool_call_id"]),
                )
                conn.execute(
                    """
                    UPDATE steps SET ended_at = ?, latency_ms = ?, status = 'completed' WHERE step_id = ?
                    """,
                    (_iso(now), lat, p["step_id"]),
                )

        self._enqueue(_write)

    def tool_error(self, *, run_id: str | None) -> None:
        if not run_id or run_id not in self._pending_tool:
            return
        p = self._pending_tool.pop(run_id)
        now = _utcnow()
        lat = int((now - p["started_at"]).total_seconds() * 1000)

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    "UPDATE tool_calls SET latency_ms = ?, status = 'failed', ended_at = ? WHERE tool_call_id = ?",
                    (lat, _iso(now), p["tool_call_id"]),
                )
                conn.execute(
                    "UPDATE steps SET ended_at = ?, latency_ms = ?, status = 'failed' WHERE step_id = ?",
                    (_iso(now), lat, p["step_id"]),
                )

        self._enqueue(_write)

    def retriever_start(
        self,
        *,
        run_id: str | None,
        parent_run_id: str | None,
        serialized: dict[str, Any] | None,
        query: Any,
    ) -> None:
        if not self._session_id or not run_id:
            return
        sid = self._session_id
        step_id = str(uuid.uuid4())
        ev_id = str(uuid.uuid4())
        parent_step = self._run_to_step.get(parent_run_id) if parent_run_id else None
        idx = self._step_index
        self._step_index += 1
        now = _utcnow()
        name = serialized_name(serialized)
        qtext = None
        if isinstance(query, str):
            qtext = query
        elif isinstance(query, dict):
            qtext = str(query.get("query") or query)

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    """
                    INSERT INTO steps (step_id, session_id, parent_step_id, step_index, step_type, started_at, ended_at, latency_ms, status, metadata_json)
                    VALUES (?, ?, ?, ?, 'retrieval', ?, NULL, NULL, 'running', ?)
                    """,
                    (step_id, sid, parent_step, idx, _iso(now), self._store.dumps({"run_id": run_id})),
                )
                conn.execute(
                    """
                    INSERT INTO retrieval_events (retrieval_event_id, step_id, retriever_name, query_text, returned_docs_count, inserted_docs_count, metadata_json, started_at, ended_at)
                    VALUES (?, ?, ?, ?, NULL, NULL, '{}', ?, NULL)
                    """,
                    (ev_id, step_id, name, qtext, _iso(now)),
                )

        self._enqueue(_write)
        self._run_to_step[run_id] = step_id
        self._pending_retrieval[run_id] = {"step_id": step_id, "ev_id": ev_id, "started_at": now}

    def retriever_end(self, *, run_id: str | None, documents: Any) -> None:
        if not run_id or run_id not in self._pending_retrieval:
            return
        p = self._pending_retrieval.pop(run_id)
        now = _utcnow()
        lat = int((now - p["started_at"]).total_seconds() * 1000)
        docs = documents or []
        cnt = len(docs) if hasattr(docs, "__len__") else None

        def _write() -> None:
            with self._store.write() as conn:
                conn.execute(
                    """
                    UPDATE retrieval_events SET returned_docs_count = ?, ended_at = ? WHERE retrieval_event_id = ?
                    """,
                    (cnt, _iso(now), p["ev_id"]),
                )
                conn.execute(
                    "UPDATE steps SET ended_at = ?, latency_ms = ?, status = 'completed' WHERE step_id = ?",
                    (_iso(now), lat, p["step_id"]),
                )

        self._enqueue(_write)

    def retriever_error(self, *, run_id: str | None) -> None:
        if not run_id or run_id not in self._pending_retrieval:
            return
        p = self._pending_retrieval.pop(run_id)
        now = _utcnow()
        lat = int((now - p["started_at"]).total_seconds() * 1000)

        def _write() -> None:
            with self._store.write() as conn:
                meta = self._store.dumps({"error": True})
                conn.execute(
                    "UPDATE retrieval_events SET metadata_json = ?, ended_at = ? WHERE retrieval_event_id = ?",
                    (meta, _iso(now), p["ev_id"]),
                )
                conn.execute(
                    "UPDATE steps SET ended_at = ?, latency_ms = ?, status = 'failed' WHERE step_id = ?",
                    (_iso(now), lat, p["step_id"]),
                )

        self._enqueue(_write)

    def refresh_findings(self) -> None:
        """Run diagnostics heuristics for the current session."""
        if not self._session_id:
            return
        sid = self._session_id
        from roomy.diagnostics.rules import compute_findings

        def _write() -> None:
            findings = compute_findings(self._store, sid)
            with self._store.write() as conn:
                conn.execute("DELETE FROM findings WHERE session_id = ?", (sid,))
                for f in findings:
                    conn.execute(
                        """
                        INSERT INTO findings (finding_id, session_id, step_id, severity, finding_type, explanation, evidence_json)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f.finding_id,
                            f.session_id,
                            f.step_id,
                            f.severity.value,
                            f.finding_type,
                            f.explanation,
                            self._store.dumps(f.evidence),
                        ),
                    )

        self._enqueue(_write)

    @staticmethod
    def _serialize_prompts(prompts: Any) -> Any:
        if prompts is None:
            return []
        if isinstance(prompts, str):
            return [{"role": "user", "content": prompts}]
        if isinstance(prompts, list) and prompts:
            first = prompts[0]
            try:
                from langchain_core.messages import BaseMessage

                if isinstance(first, BaseMessage):
                    out = []
                    for m in prompts:
                        d = m.model_dump() if hasattr(m, "model_dump") else {"content": str(m)}
                        out.append(d)
                    return out
            except Exception:
                pass
        return prompts

    @staticmethod
    def _prompts_summary(prompts: Any) -> str:
        try:
            s = str(prompts)
            return s[:500] + ("…" if len(s) > 500 else "")
        except Exception:
            return ""
