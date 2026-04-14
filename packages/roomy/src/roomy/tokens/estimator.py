from __future__ import annotations

import math
from typing import Any


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Rough heuristic pricing (USD) for local debugging only."""
    m = model.lower()
    # Approximate list — not authoritative
    if "gpt-4o-mini" in m:
        return (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
    if "gpt-4o" in m:
        return (input_tokens * 2.50 + output_tokens * 10.00) / 1_000_000
    if "gpt-3.5" in m:
        return (input_tokens * 0.50 + output_tokens * 1.50) / 1_000_000
    if "claude-3-5-sonnet" in m or "claude-3-5-sonnet" in m:
        return (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000
    if "claude" in m:
        return (input_tokens * 3.0 + output_tokens * 15.0) / 1_000_000
    if "gemini" in m:
        return (input_tokens * 0.50 + output_tokens * 1.50) / 1_000_000
    return None


class TokenEstimator:
    """Prefer tiktoken when installed; otherwise char-based fallback."""

    def __init__(self, model_hint: str | None = None) -> None:
        self._model_hint = model_hint or "gpt-4o-mini"
        self._encoding = None
        try:
            import tiktoken

            try:
                self._encoding = tiktoken.encoding_for_model(self._model_hint)
            except Exception:
                self._encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            self._encoding = None

    def count(self, text: str) -> int:
        if not text:
            return 0
        if self._encoding is not None:
            return len(self._encoding.encode(text))
        return max(1, math.ceil(len(text) / 4))

    def count_messages(self, messages: list[Any]) -> int:
        total = 0
        for m in messages:
            if isinstance(m, str):
                total += self.count(m)
                continue
            if not isinstance(m, dict):
                total += self.count(str(m))
                continue
            content = m.get("content")
            if isinstance(content, str):
                total += self.count(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        total += self.count(str(part.get("text", "")))
                    else:
                        total += self.count(str(part))
            else:
                total += self.count(str(content))
        return total
