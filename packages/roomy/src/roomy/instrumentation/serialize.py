from __future__ import annotations

from typing import Any

from langchain_core.outputs import LLMResult


def llm_result_to_dict(result: LLMResult) -> dict[str, Any]:
    out: dict[str, Any] = {"generations": []}
    for gen_list in result.generations:
        row: list[dict[str, Any]] = []
        for g in gen_list:
            if isinstance(g, str):
                row.append({"text": g, "generation_info": {}})
                continue
            msg = getattr(g, "message", None)
            text = getattr(g, "text", None)
            gi = getattr(g, "generation_info", None) or {}
            if not isinstance(gi, dict):
                gi = {}
            item: dict[str, Any] = {"generation_info": gi}
            if msg is not None:
                try:
                    item["message"] = msg.model_dump()
                except Exception:
                    item["message"] = str(msg)
            if text is not None:
                item["text"] = text
            row.append(item)
        out["generations"].append(row)
    if isinstance(result.llm_output, dict) and result.llm_output:
        out["llm_output"] = dict(result.llm_output)
    return out


def token_usage_from_llm_result(result: LLMResult) -> tuple[int | None, int | None, int | None]:
    inp = out = cached = None
    lo = result.llm_output if isinstance(result.llm_output, dict) else {}
    usage = lo.get("token_usage") or lo.get("usage")
    if isinstance(usage, dict):
        inp = usage.get("prompt_tokens") or usage.get("input_tokens")
        out = usage.get("completion_tokens") or usage.get("output_tokens")
        cached = usage.get("cached_tokens")
    if inp is None and result.generations:
        for gen_list in result.generations:
            for g in gen_list:
                if isinstance(g, str):
                    continue
                gi = getattr(g, "generation_info", None) or {}
                if isinstance(gi, dict):
                    u = gi.get("token_usage") or gi.get("usage_metadata")
                    if isinstance(u, dict):
                        inp = inp or u.get("prompt_tokens") or u.get("input_tokens")
                        out = out or u.get("completion_tokens") or u.get("output_tokens")
    return (
        int(inp) if inp is not None else None,
        int(out) if out is not None else None,
        int(cached) if cached is not None else None,
    )


def serialized_name(serialized: dict[str, Any] | None) -> str:
    if not serialized:
        return "unknown"
    try:
        return str(serialized.get("name") or serialized.get("id") or "unknown")
    except Exception:
        return "unknown"
