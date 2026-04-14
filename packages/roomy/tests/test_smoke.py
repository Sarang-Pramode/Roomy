from roomy.instrumentation.manager import TraceManager
from roomy.storage.sqlite_store import SqliteStore


def test_sqlite_store_migrations(tmp_path) -> None:
    p = tmp_path / "t.db"
    store = SqliteStore(str(p))
    rows = store.query_all("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    names = {r["name"] for r in rows}
    assert "sessions" in names
    assert "context_segments" in names
    store.close()


def test_trace_manager_session(tmp_path) -> None:
    from roomy.config.settings import RoomyConfig

    p = tmp_path / "t.db"
    store = SqliteStore(str(p))
    mgr = TraceManager(store, RoomyConfig())
    sid = mgr.start_session("test-agent")
    mgr.flush()
    row = store.query_one("SELECT * FROM sessions WHERE session_id = ?", (sid,))
    assert row is not None
    mgr.end_session()
    mgr.flush()
