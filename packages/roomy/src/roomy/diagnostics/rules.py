from __future__ import annotations

import uuid

from roomy.schema.models import Finding, FindingSeverity
from roomy.storage.sqlite_store import SqliteStore


def compute_findings(store: SqliteStore, session_id: str) -> list[Finding]:
    findings: list[Finding] = []
    rows = store.query_all(
        """
        SELECT tc.tool_call_id, tc.step_id, tc.tool_name, tc.output_size_bytes, tc.tool_output_preview
        FROM tool_calls tc
        JOIN steps s ON s.step_id = tc.step_id
        WHERE s.session_id = ?
        """,
        (session_id,),
    )
    for r in rows:
        size = int(r["output_size_bytes"] or 0)
        if size > 8000:
            findings.append(
                Finding(
                    finding_id=str(uuid.uuid4()),
                    session_id=session_id,
                    step_id=r["step_id"],
                    severity=FindingSeverity.warning,
                    finding_type="oversized_tool_output",
                    explanation=f"Tool '{r['tool_name']}' produced ~{size} bytes of output.",
                    evidence={"tool_call_id": r["tool_call_id"], "output_size_bytes": size},
                )
            )

    seg_rows = store.query_all(
        """
        SELECT cs.full_text, cs.segment_type, lc.step_id, s.step_index
        FROM context_segments cs
        JOIN llm_calls lc ON lc.llm_call_id = cs.llm_call_id
        JOIN steps s ON s.step_id = lc.step_id
        WHERE s.session_id = ? AND cs.full_text IS NOT NULL
        ORDER BY s.step_index, cs.order_index
        """,
        (session_id,),
    )
    seen: dict[str, int] = {}
    for r in seg_rows:
        text = r["full_text"] or ""
        if len(text) < 80:
            continue
        key = text[:200]
        seen[key] = seen.get(key, 0) + 1
    for key, count in seen.items():
        if count >= 3:
            findings.append(
                Finding(
                    finding_id=str(uuid.uuid4()),
                    session_id=session_id,
                    step_id=None,
                    severity=FindingSeverity.info,
                    finding_type="repeated_segment",
                    explanation="Similar context segment text appears across multiple steps.",
                    evidence={"approx_repeats": count, "sample": key[:120]},
                )
            )
            break

    hist = store.query_all(
        """
        SELECT SUM(cs.token_count) AS tok, lc.llm_call_id
        FROM context_segments cs
        JOIN llm_calls lc ON lc.llm_call_id = cs.llm_call_id
        JOIN steps s ON s.step_id = lc.step_id
        WHERE s.session_id = ? AND cs.segment_type = 'conversation_history'
        GROUP BY lc.llm_call_id
        """,
        (session_id,),
    )
    for r in hist:
        total_row = store.query_one(
            """
            SELECT SUM(cs.token_count) AS total
            FROM context_segments cs
            WHERE cs.llm_call_id = ?
            """,
            (r["llm_call_id"],),
        )
        total = int(total_row["total"] or 0) if total_row else 0
        htok = int(r["tok"] or 0)
        if total > 0 and htok / total >= 0.5:
            step_row = store.query_one(
                "SELECT step_id FROM llm_calls WHERE llm_call_id = ?",
                (r["llm_call_id"],),
            )
            findings.append(
                Finding(
                    finding_id=str(uuid.uuid4()),
                    session_id=session_id,
                    step_id=step_row["step_id"] if step_row else None,
                    severity=FindingSeverity.info,
                    finding_type="history_dominated",
                    explanation="Conversation/history segments account for more than half of estimated input tokens.",
                    evidence={"llm_call_id": r["llm_call_id"], "history_tokens": htok, "total_tokens": total},
                )
            )
            break

    tok_row = store.query_one(
        """
        SELECT SUM(COALESCE(input_tokens_estimated, input_tokens_reported, 0)) AS inp
        FROM llm_calls lc
        JOIN steps s ON s.step_id = lc.step_id
        WHERE s.session_id = ?
        """,
        (session_id,),
    )
    inp = int(tok_row["inp"] or 0) if tok_row else 0
    if inp > 100_000:
        findings.append(
            Finding(
                finding_id=str(uuid.uuid4()),
                session_id=session_id,
                step_id=None,
                severity=FindingSeverity.warning,
                finding_type="context_overflow_risk",
                explanation="Session cumulative estimated input tokens are very high; watch provider limits.",
                evidence={"cumulative_input_tokens": inp},
            )
        )

    return findings


def export_session_markdown(store: SqliteStore, session_id: str) -> str:
    s = store.query_one("SELECT * FROM sessions WHERE session_id = ?", (session_id,))
    if not s:
        return ""
    lines = [
        f"# Roomy session {session_id}",
        f"- Agent: {s['agent_name']}",
        f"- Status: {s['status']}",
        f"- Started: {s['started_at']}",
        "",
        "## Steps",
    ]
    steps = store.query_all(
        "SELECT * FROM steps WHERE session_id = ? ORDER BY step_index",
        (session_id,),
    )
    for st in steps:
        lines.append(f"- **{st['step_index']}** `{st['step_type']}` {st['step_id'][:8]}… latency={st['latency_ms']}ms")
    lines.append("")
    lines.append("## Findings")
    fs = store.query_all("SELECT * FROM findings WHERE session_id = ?", (session_id,))
    for f in fs:
        lines.append(f"- [{f['severity']}] {f['finding_type']}: {f['explanation']}")
    return "\n".join(lines)
