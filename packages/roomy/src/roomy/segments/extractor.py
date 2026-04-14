from __future__ import annotations

import uuid
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    ChatMessage,
    FunctionMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)

from roomy.schema.models import ContextSegment, ContextSegmentType
from roomy.tokens.estimator import TokenEstimator


def _message_text(msg: BaseMessage) -> str:
    c = msg.content
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts: list[str] = []
        for p in c:
            if isinstance(p, dict) and p.get("type") == "text":
                parts.append(str(p.get("text", "")))
            else:
                parts.append(str(p))
        return "\n".join(parts)
    return str(c)


def _classify(msg: BaseMessage) -> ContextSegmentType:
    if isinstance(msg, SystemMessage):
        return ContextSegmentType.system_prompt
    if isinstance(msg, HumanMessage):
        return ContextSegmentType.user_message
    if isinstance(msg, AIMessage):
        return ContextSegmentType.conversation_history
    if isinstance(msg, ToolMessage):
        return ContextSegmentType.tool_result
    if isinstance(msg, FunctionMessage):
        return ContextSegmentType.tool_result
    if isinstance(msg, ChatMessage):
        role = (msg.role or "").lower()
        if role == "system":
            return ContextSegmentType.system_prompt
        if role == "developer":
            return ContextSegmentType.developer_prompt
        return ContextSegmentType.conversation_history
    return ContextSegmentType.unknown


def _messages_from_prompts(prompts: list[str] | Any) -> list[BaseMessage]:
    if not prompts:
        return []
    first = prompts[0]
    if isinstance(first, BaseMessage):
        return list(prompts)  # type: ignore[arg-type]
    if isinstance(first, list):
        inner = first
        if inner and isinstance(inner[0], BaseMessage):
            return list(inner)  # type: ignore[arg-type]
    if isinstance(first, str):
        return [HumanMessage(content=p) for p in prompts]  # type: ignore[list-item]
    return []


class ContextSegmentExtractor:
    def __init__(self, model_hint: str | None = None) -> None:
        self._estimator = TokenEstimator(model_hint=model_hint)

    def extract(self, llm_call_id: str, prompts: Any) -> tuple[list[ContextSegment], dict[str, Any]]:
        msgs = _messages_from_prompts(prompts)
        segments: list[ContextSegment] = []
        order = 0
        for msg in msgs:
            text = _message_text(msg)
            stype = _classify(msg)
            preview = text[:500] + ("…" if len(text) > 500 else "")
            tok = self._estimator.count(text)
            seg = ContextSegment(
                segment_id=str(uuid.uuid4()),
                llm_call_id=llm_call_id,
                order_index=order,
                segment_type=stype,
                source_kind=msg.__class__.__name__,
                source_name=getattr(msg, "name", None),
                text_preview=preview,
                full_text=text,
                token_count=tok,
                byte_count=len(text.encode("utf-8")),
            )
            segments.append(seg)
            order += 1

        by_type: dict[str, int] = {}
        for s in segments:
            k = s.segment_type.value
            by_type[k] = by_type.get(k, 0) + (s.token_count or 0)
        total_in = sum(s.token_count or 0 for s in segments)
        top = sorted(segments, key=lambda s: s.token_count or 0, reverse=True)[:3]
        summary = {
            "total_input_tokens_estimated": total_in,
            "percent_by_segment_type": {
                k: round(100 * v / total_in, 2) if total_in else 0.0 for k, v in by_type.items()
            },
            "top_segments": [
                {"segment_type": s.segment_type.value, "token_count": s.token_count}
                for s in top
            ],
        }
        return segments, summary


def extract_segments_for_llm_call(
    llm_call_id: str, prompts: Any, model_hint: str | None
) -> tuple[list[ContextSegment], dict[str, Any]]:
    return ContextSegmentExtractor(model_hint=model_hint).extract(llm_call_id, prompts)
