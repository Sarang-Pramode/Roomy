from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from roomy.redaction.pipeline import RedactionConfig


@dataclass
class RoomyConfig:
    db_path: str = "./roomy_traces.db"
    redaction: RedactionConfig | None = None
    capture_raw: bool = True
    extra: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if self.redaction is None:
            self.redaction = RedactionConfig()
        if self.extra is None:
            self.extra = {}


def load_config(path: str | Path | None = None) -> RoomyConfig:
    p = path or os.environ.get("ROOMY_CONFIG")
    if not p:
        return RoomyConfig(db_path=os.environ.get("ROOMY_DB_PATH", "./roomy_traces.db"))
    pp = Path(p)
    if not pp.exists():
        return RoomyConfig()
    data = yaml.safe_load(pp.read_text()) or {}
    red = data.get("redaction") or {}
    cfg = RoomyConfig(
        db_path=data.get("db_path", "./roomy_traces.db"),
        redaction=RedactionConfig(
            enabled=red.get("enabled", True),
            pii_email=red.get("pii_email", False),
            store_full_text=red.get("store_full_text", True),
        ),
        capture_raw=data.get("capture_raw", True),
        extra={k: v for k, v in data.items() if k not in {"db_path", "redaction", "capture_raw"}},
    )
    return cfg
