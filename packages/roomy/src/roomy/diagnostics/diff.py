from __future__ import annotations

from typing import Any


def diff_llm_segments(
    prev: list[dict[str, Any]],
    nxt: list[dict[str, Any]],
) -> dict[str, Any]:
    """Compare ordered context segments between two LLM calls (dict rows from DB/API)."""

    def key(r: dict[str, Any]) -> tuple:
        return (r.get("order_index"), r.get("segment_type"), r.get("text_preview") or "")

    prev_m = {key(r): r for r in prev}
    next_m = {key(r): r for r in nxt}
    added = [r for k, r in next_m.items() if k not in prev_m]
    removed = [r for k, r in prev_m.items() if k not in next_m]
    token_delta = 0
    for r in nxt:
        token_delta += int(r.get("token_count") or 0)
    for r in prev:
        token_delta -= int(r.get("token_count") or 0)
    return {
        "added_segments": added,
        "removed_segments": removed,
        "token_count_delta": token_delta,
    }
