from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AuditJournal:
    """Append-only JSONL audit trail for approvals, rejections, and executions."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, event_type: str, payload: dict[str, Any]) -> None:
        event = {
            "ts": datetime.now(UTC).isoformat(),
            "event_type": event_type,
            "payload": _safe(payload),
        }
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")


def _safe(value: Any) -> Any:
    if is_dataclass(value):
        return _safe(asdict(value))
    if isinstance(value, dict):
        return {str(k): _safe(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [_safe(item) for item in value]
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    return value
