"""Heuristic linking of tool/retrieval steps to the LLM call that follows them in a session."""

from __future__ import annotations

from typing import Any

from roomy.storage.sqlite_store import SqliteStore


def list_upstream_context_steps(store: SqliteStore, step_id: str) -> list[dict[str, Any]] | None:
    """
    For an **LLM** step, return tool/retrieval (and memory) steps that ran **after** the previous LLM
    step in the same session and **before** this LLM step. This approximates “context that likely fed
    this model call” when LangChain orders callbacks by step_index.
    """
    st = store.query_one("SELECT * FROM steps WHERE step_id = ?", (step_id,))
    if not st:
        return None
    if st["step_type"] != "llm":
        return []

    session_id = st["session_id"]
    idx = int(st["step_index"])
    prev = store.query_one(
        """
        SELECT MAX(step_index) AS m FROM steps
        WHERE session_id = ? AND step_type = 'llm' AND step_index < ?
        """,
        (session_id, idx),
    )
    prev_idx = int(prev["m"]) if prev and prev["m"] is not None else -1

    rows = store.query_all(
        """
        SELECT * FROM steps
        WHERE session_id = ? AND step_index > ? AND step_index < ?
          AND step_type IN ('tool', 'retrieval', 'memory')
        ORDER BY step_index
        """,
        (session_id, prev_idx, idx),
    )
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        sid = r["step_id"]
        stype = r["step_type"]
        if stype == "tool":
            tc = store.query_all(
                """
                SELECT tool_call_id, tool_name, output_size_bytes, latency_ms, status,
                  substr(tool_output_preview, 1, 200) AS tool_output_preview
                FROM tool_calls WHERE step_id = ?
                """,
                (sid,),
            )
            d["tool_calls"] = [dict(x) for x in tc]
        elif stype == "retrieval":
            re = store.query_all(
                """
                SELECT retrieval_event_id, retriever_name, query_text, returned_docs_count
                FROM retrieval_events WHERE step_id = ?
                """,
                (sid,),
            )
            d["retrieval_events"] = [dict(x) for x in re]
        out.append(d)
    return out
