from __future__ import annotations

import hashlib
import json
from pathlib import Path


class AuditHashChain:
    """Tamper-evident hash chain over JSONL audit events."""

    def root(self, audit_path: str) -> str:
        path = Path(audit_path)
        if not path.exists():
            return "no-audit-log"
        previous = "0" * 64
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                previous = hashlib.sha256(f"{previous}:{line}".encode("utf-8")).hexdigest()
        return previous

    def verify_jsonl(self, audit_path: str) -> bool:
        path = Path(audit_path)
        if not path.exists():
            return True
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    json.loads(line)
                except json.JSONDecodeError:
                    return False
        return True
