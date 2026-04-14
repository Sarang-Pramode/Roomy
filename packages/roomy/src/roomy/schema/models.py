from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class SessionStatus(StrEnum):
    running = "running"
    completed = "completed"
    failed = "failed"


class StepType(StrEnum):
    llm = "llm"
    tool = "tool"
    retrieval = "retrieval"
    memory = "memory"
    control = "control"


class StepStatus(StrEnum):
    running = "running"
    completed = "completed"
    failed = "failed"


class ContextSegmentType(StrEnum):
    system_prompt = "system_prompt"
    developer_prompt = "developer_prompt"
    user_message = "user_message"
    conversation_history = "conversation_history"
    memory_summary = "memory_summary"
    retrieved_document = "retrieved_document"
    tool_definition = "tool_definition"
    tool_result = "tool_result"
    scratchpad = "scratchpad"
    output_parser_instructions = "output_parser_instructions"
    guardrail_prompt = "guardrail_prompt"
    image = "image"
    unknown = "unknown"


class FindingSeverity(StrEnum):
    info = "info"
    warning = "warning"
    error = "error"


class Session(BaseModel):
    session_id: str
    agent_name: str
    environment: str = "dev"
    started_at: datetime
    ended_at: datetime | None = None
    status: SessionStatus = SessionStatus.running
    metadata: dict[str, Any] = Field(default_factory=dict)


class Step(BaseModel):
    step_id: str
    session_id: str
    parent_step_id: str | None = None
    step_index: int
    step_type: StepType
    started_at: datetime
    ended_at: datetime | None = None
    latency_ms: int | None = None
    status: StepStatus = StepStatus.running
    metadata: dict[str, Any] = Field(default_factory=dict)


class LLMCall(BaseModel):
    llm_call_id: str
    step_id: str
    provider: str = "unknown"
    model: str = "unknown"
    request_payload_raw: dict[str, Any] | None = None
    response_payload_raw: dict[str, Any] | None = None
    input_tokens_reported: int | None = None
    output_tokens_reported: int | None = None
    input_tokens_estimated: int | None = None
    output_tokens_estimated: int | None = None
    cached_tokens: int | None = None
    cost_estimate_usd: float | None = None
    reconciliation_status: str | None = None
    segment_summary_json: dict[str, Any] | None = None


class ToolCall(BaseModel):
    tool_call_id: str
    step_id: str
    tool_name: str
    tool_args: dict[str, Any] | str | None = None
    tool_output_preview: str | None = None
    output_size_bytes: int | None = None
    latency_ms: int | None = None
    status: str = "completed"
    metadata: dict[str, Any] = Field(default_factory=dict)


class RetrievalEvent(BaseModel):
    retrieval_event_id: str
    step_id: str
    retriever_name: str = "unknown"
    query_text: str | None = None
    returned_docs_count: int | None = None
    inserted_docs_count: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextSegment(BaseModel):
    segment_id: str
    llm_call_id: str
    order_index: int
    segment_type: ContextSegmentType
    source_kind: str | None = None
    source_name: str | None = None
    text_preview: str | None = None
    full_text: str | None = None
    token_count: int | None = None
    byte_count: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    finding_id: str
    session_id: str
    step_id: str | None = None
    severity: FindingSeverity
    finding_type: str
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)
