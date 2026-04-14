from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import Any

from roomy.storage.migrations import apply_migrations


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


class SqliteStore:
    """Thread-safe SQLite access for trace persistence."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        apply_migrations(self._conn)

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    @contextmanager
    def write(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                yield self._conn
                self._conn.commit()
            except Exception:
                self._conn.rollback()
                raise

    def execute(self, sql: str, params: tuple[Any, ...] | list[Any] = ()) -> sqlite3.Cursor:
        with self._lock:
            cur = self._conn.execute(sql, params)
            self._conn.commit()
            return cur

    def query_one(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Row | None:
        with self._lock:
            cur = self._conn.execute(sql, params)
            return cur.fetchone()

    def query_all(self, sql: str, params: tuple[Any, ...] = ()) -> list[sqlite3.Row]:
        with self._lock:
            cur = self._conn.execute(sql, params)
            return list(cur.fetchall())

    @staticmethod
    def dumps(obj: Any) -> str:
        return json.dumps(obj, default=str)

    @staticmethod
    def loads(s: str | None) -> Any:
        if s is None:
            return None
        return json.loads(s)
