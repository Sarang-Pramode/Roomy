from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1

DDL_V1 = """
CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY,
  agent_name TEXT NOT NULL,
  environment TEXT NOT NULL DEFAULT 'dev',
  started_at TEXT NOT NULL,
  ended_at TEXT,
  status TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS steps (
  step_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  parent_step_id TEXT REFERENCES steps(step_id) ON DELETE SET NULL,
  step_index INTEGER NOT NULL,
  step_type TEXT NOT NULL,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  latency_ms INTEGER,
  status TEXT NOT NULL,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  UNIQUE(session_id, step_index)
);

CREATE INDEX IF NOT EXISTS idx_steps_session ON steps(session_id);

CREATE TABLE IF NOT EXISTS llm_calls (
  llm_call_id TEXT PRIMARY KEY,
  step_id TEXT NOT NULL REFERENCES steps(step_id) ON DELETE CASCADE,
  provider TEXT NOT NULL DEFAULT 'unknown',
  model TEXT NOT NULL DEFAULT 'unknown',
  request_payload_json TEXT,
  response_payload_json TEXT,
  input_tokens_reported INTEGER,
  output_tokens_reported INTEGER,
  input_tokens_estimated INTEGER,
  output_tokens_estimated INTEGER,
  cached_tokens INTEGER,
  cost_estimate_usd REAL,
  reconciliation_status TEXT,
  segment_summary_json TEXT,
  started_at TEXT,
  ended_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_llm_calls_step ON llm_calls(step_id);

CREATE TABLE IF NOT EXISTS tool_calls (
  tool_call_id TEXT PRIMARY KEY,
  step_id TEXT NOT NULL REFERENCES steps(step_id) ON DELETE CASCADE,
  tool_name TEXT NOT NULL,
  tool_args_json TEXT,
  tool_output_preview TEXT,
  output_size_bytes INTEGER,
  latency_ms INTEGER,
  status TEXT NOT NULL DEFAULT 'completed',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  started_at TEXT,
  ended_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_tool_calls_step ON tool_calls(step_id);

CREATE TABLE IF NOT EXISTS retrieval_events (
  retrieval_event_id TEXT PRIMARY KEY,
  step_id TEXT NOT NULL REFERENCES steps(step_id) ON DELETE CASCADE,
  retriever_name TEXT NOT NULL DEFAULT 'unknown',
  query_text TEXT,
  returned_docs_count INTEGER,
  inserted_docs_count INTEGER,
  metadata_json TEXT NOT NULL DEFAULT '{}',
  started_at TEXT,
  ended_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_retrieval_step ON retrieval_events(step_id);

CREATE TABLE IF NOT EXISTS context_segments (
  segment_id TEXT PRIMARY KEY,
  llm_call_id TEXT NOT NULL REFERENCES llm_calls(llm_call_id) ON DELETE CASCADE,
  order_index INTEGER NOT NULL,
  segment_type TEXT NOT NULL,
  source_kind TEXT,
  source_name TEXT,
  text_preview TEXT,
  full_text TEXT,
  token_count INTEGER,
  byte_count INTEGER,
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_segments_llm ON context_segments(llm_call_id);

CREATE TABLE IF NOT EXISTS findings (
  finding_id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
  step_id TEXT REFERENCES steps(step_id) ON DELETE CASCADE,
  severity TEXT NOT NULL,
  finding_type TEXT NOT NULL,
  explanation TEXT NOT NULL,
  evidence_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_findings_session ON findings(session_id);
"""


def apply_migrations(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA user_version")
    row = cur.fetchone()
    version = int(row[0]) if row and row[0] is not None else 0
    if version < 1:
        cur.executescript(DDL_V1)
        cur.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        conn.commit()
    elif version > SCHEMA_VERSION:
        raise RuntimeError(f"Database schema v{version} is newer than roomy supports ({SCHEMA_VERSION})")


def current_schema_version() -> int:
    return SCHEMA_VERSION
