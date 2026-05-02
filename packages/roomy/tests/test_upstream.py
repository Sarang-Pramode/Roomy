from roomy.api.upstream import list_upstream_context_steps
from roomy.config.settings import RoomyConfig
from roomy.instrumentation.manager import TraceManager
from roomy.storage.sqlite_store import SqliteStore


def test_upstream_between_llm_calls(tmp_path) -> None:
    """Tool step between two LLM steps is attributed to the second LLM."""
    db = tmp_path / "t.db"
    store = SqliteStore(str(db))
    mgr = TraceManager(store, RoomyConfig())
    sid = mgr.start_session("test")
    mgr.flush()

    # Insert minimal steps: llm @0, tool @1, llm @2 (simulate ordering)
    import uuid

    s1, s2, s3 = str(uuid.uuid4()), str(uuid.uuid4()), str(uuid.uuid4())
    with store.write() as conn:
        conn.execute(
            """
            INSERT INTO steps (step_id, session_id, parent_step_id, step_index, step_type, started_at, ended_at, latency_ms, status, metadata_json)
            VALUES (?, ?, NULL, 0, 'llm', '2026-01-01T00:00:00Z', '2026-01-01T00:00:01Z', 1, 'completed', '{}')
            """,
            (s1, sid),
        )
        conn.execute(
            """
            INSERT INTO steps (step_id, session_id, parent_step_id, step_index, step_type, started_at, ended_at, latency_ms, status, metadata_json)
            VALUES (?, ?, NULL, 1, 'tool', '2026-01-01T00:00:01Z', '2026-01-01T00:00:02Z', 1, 'completed', '{}')
            """,
            (s2, sid),
        )
        conn.execute(
            """
            INSERT INTO steps (step_id, session_id, parent_step_id, step_index, step_type, started_at, ended_at, latency_ms, status, metadata_json)
            VALUES (?, ?, NULL, 2, 'llm', '2026-01-01T00:00:02Z', '2026-01-01T00:00:03Z', 1, 'completed', '{}')
            """,
            (s3, sid),
        )
        tid = str(uuid.uuid4())
        conn.execute(
            """
            INSERT INTO tool_calls (tool_call_id, step_id, tool_name, tool_args_json, tool_output_preview, output_size_bytes, latency_ms, status, metadata_json, started_at, ended_at)
            VALUES (?, ?, 'demo_tool', '{}', 'out', 3, 1, 'completed', '{}', '2026-01-01T00:00:01Z', '2026-01-01T00:00:02Z')
            """,
            (tid, s2),
        )

    up = list_upstream_context_steps(store, s3)
    assert up is not None
    assert len(up) == 1
    assert up[0]["step_id"] == s2
    assert up[0]["tool_calls"][0]["tool_name"] == "demo_tool"


def test_upstream_non_llm_returns_empty(tmp_path) -> None:
    db = tmp_path / "t2.db"
    store = SqliteStore(str(db))
    mgr = TraceManager(store, RoomyConfig())
    sid = mgr.start_session("x")
    mgr.flush()
    import uuid

    tid = str(uuid.uuid4())
    with store.write() as conn:
        conn.execute(
            """
            INSERT INTO steps (step_id, session_id, parent_step_id, step_index, step_type, started_at, ended_at, latency_ms, status, metadata_json)
            VALUES (?, ?, NULL, 0, 'tool', '2026-01-01T00:00:00Z', '2026-01-01T00:00:01Z', 1, 'completed', '{}')
            """,
            (tid, sid),
        )
    assert list_upstream_context_steps(store, tid) == []
