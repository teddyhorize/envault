"""Export audit log entries to JSON or CSV format."""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import List, Optional

from envault.audit import AuditLog, AuditEntry


class AuditExportError(Exception):
    """Raised when audit export fails."""


SUPPORTED_FORMATS = ("json", "csv")


def export_audit_log(
    vault_path: str,
    password: str,
    fmt: str = "json",
    output_path: Optional[str] = None,
) -> str:
    """Export audit log entries to the given format.

    Args:
        vault_path: Path to the vault file.
        password: Vault password (used to open the audit log).
        fmt: Output format — 'json' or 'csv'.
        output_path: If provided, write output to this file path.

    Returns:
        The serialised audit log as a string.

    Raises:
        AuditExportError: If the format is unsupported or export fails.
    """
    if fmt not in SUPPORTED_FORMATS:
        raise AuditExportError(
            f"Unsupported format '{fmt}'. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )

    try:
        log = AuditLog(vault_path, password)
        entries: List[AuditEntry] = log.entries()
    except Exception as exc:
        raise AuditExportError(f"Failed to read audit log: {exc}") from exc

    if fmt == "json":
        payload = json.dumps([e.to_dict() for e in entries], indent=2)
    else:
        buf = io.StringIO()
        fieldnames = ["timestamp", "action", "key", "user", "detail"]
        writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for entry in entries:
            row = entry.to_dict()
            row.setdefault("user", "")
            row.setdefault("detail", "")
            writer.writerow(row)
        payload = buf.getvalue()

    if output_path:
        Path(output_path).write_text(payload, encoding="utf-8")

    return payload
