from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from langchain_core.runnables import Runnable, RunnableConfig

from roomy.config.settings import RoomyConfig, load_config
from roomy.instrumentation.callbacks import RoomyAsyncCallbackHandler, RoomyCallbackHandler
from roomy.instrumentation.manager import TraceManager
from roomy.storage.sqlite_store import SqliteStore


def _default_db_path() -> str:
    return os.environ.get("ROOMY_DB_PATH", "./roomy_traces.db")


@dataclass
class RoomyBindings:
    """Return value from `instrument_langchain`."""

    manager: TraceManager
    callbacks: list[Any]


def instrument_langchain(
    *,
    app_name: str,
    environment: str | None = None,
    db_path: str | None = None,
    config: RoomyConfig | None = None,
    metadata: dict[str, Any] | None = None,
    async_handler: bool = False,
) -> RoomyBindings:
    """
    Start a Roomy trace session. Pass ``bindings.callbacks`` to LangChain ``config``/``callbacks``.
    """
    cfg = config or load_config()
    path = db_path or cfg.db_path or _default_db_path()
    store = SqliteStore(path)
    mgr = TraceManager(store, cfg)
    env = environment or os.environ.get("ROOMY_ENV", "dev")
    mgr.start_session(app_name, environment=env, metadata=metadata)
    h: RoomyCallbackHandler | RoomyAsyncCallbackHandler
    if async_handler:
        h = RoomyAsyncCallbackHandler(mgr)
    else:
        h = RoomyCallbackHandler(mgr)
    return RoomyBindings(manager=mgr, callbacks=[h])


def make_handler(
    manager: TraceManager,
    *,
    async_handler: bool = False,
) -> RoomyCallbackHandler | RoomyAsyncCallbackHandler:
    if async_handler:
        return RoomyAsyncCallbackHandler(manager)
    return RoomyCallbackHandler(manager)


def wrap_agent(agent: Runnable, manager: TraceManager, *, async_handler: bool = False) -> Runnable:
    """Bind Roomy callbacks onto a Runnable (agent) default config."""

    h = make_handler(manager, async_handler=async_handler)
    return agent.with_config(RunnableConfig(callbacks=[h]))


def end_session(manager: TraceManager, *, failed: bool = False) -> None:
    manager.flush()
    manager.end_session("failed" if failed else "completed")
    manager.flush()
    try:
        manager.refresh_findings()
        manager.flush()
    except Exception:
        pass
