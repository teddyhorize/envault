"""Audit log for tracking vault operations."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

AUDIT_LOG_FILENAME = ".envault_audit.json"


class AuditEntry:
    """Represents a single audit log entry."""

    def __init__(self, action: str, key: Optional[str], actor: str, timestamp: Optional[str] = None):
        self.action = action
        self.key = key
        self.actor = actor
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "action": self.action,
            "key": self.key,
            "actor": self.actor,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AuditEntry":
        return cls(
            action=data["action"],
            key=data.get("key"),
            actor=data["actor"],
            timestamp=data["timestamp"],
        )

    def __repr__(self) -> str:
        return f"AuditEntry(action={self.action!r}, key={self.key!r}, actor={self.actor!r})"


class AuditLog:
    """Persistent append-only audit log stored alongside the vault."""

    def __init__(self, vault_path: str):
        vault_dir = Path(vault_path).parent
        self.log_path = vault_dir / AUDIT_LOG_FILENAME

    def record(self, action: str, key: Optional[str] = None, actor: Optional[str] = None) -> None:
        """Append a new entry to the audit log."""
        resolved_actor = actor or os.environ.get("USER", "unknown")
        entry = AuditEntry(action=action, key=key, actor=resolved_actor)
        entries = self._load_entries()
        entries.append(entry.to_dict())
        self.log_path.write_text(json.dumps(entries, indent=2))

    def entries(self) -> List[AuditEntry]:
        """Return all recorded audit entries."""
        return [AuditEntry.from_dict(d) for d in self._load_entries()]

    def clear(self) -> None:
        """Remove all audit log entries."""
        if self.log_path.exists():
            self.log_path.unlink()

    def _load_entries(self) -> list:
        if not self.log_path.exists():
            return []
        try:
            return json.loads(self.log_path.read_text())
        except (json.JSONDecodeError, OSError):
            return []
