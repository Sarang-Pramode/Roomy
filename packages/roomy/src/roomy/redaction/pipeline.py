from __future__ import annotations

import copy
import re
from dataclasses import dataclass, field
from typing import Any

_KEY_PATTERNS = (
    r"(?i)(api[_-]?key|authorization|password|secret|token|bearer)",
)


@dataclass
class RedactionConfig:
    enabled: bool = True
    mask_keys_regex: str = "|".join(_KEY_PATTERNS)
    pii_email: bool = False
    store_full_text: bool = True

    compiled: re.Pattern[str] | None = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.compiled = re.compile(self.mask_keys_regex) if self.mask_keys_regex else None


def redact_text(text: str, cfg: RedactionConfig | None) -> str:
    if not text or cfg is None or not cfg.enabled:
        return text
    out = text
    if cfg.pii_email:
        out = re.sub(
            r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}",
            "[REDACTED_EMAIL]",
            out,
            flags=re.I,
        )
    return out


def redact_json(obj: Any, cfg: RedactionConfig | None) -> Any:
    if cfg is None or not cfg.enabled:
        return obj
    if isinstance(obj, dict):
        new: dict[str, Any] = {}
        for k, v in obj.items():
            key = str(k)
            if cfg.compiled and cfg.compiled.search(key):
                new[key] = "[REDACTED]"
            else:
                new[key] = redact_json(v, cfg)
        return new
    if isinstance(obj, list):
        return [redact_json(x, cfg) for x in obj]
    if isinstance(obj, str):
        return redact_text(obj, cfg)
    return copy.deepcopy(obj)
