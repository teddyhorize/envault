"""Secret version history tracking for envault."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Optional

from envault.vault import Vault


class HistoryError(Exception):
    """Raised when a history operation fails."""


def _history_path(vault: Vault) -> Path:
    return Path(vault.path).parent / (Path(vault.path).stem + ".history.json")


def _load_history(vault: Vault) -> dict:
    p = _history_path(vault)
    if not p.exists():
        return {}
    with p.open("r") as f:
        return json.load(f)


def _save_history(vault: Vault, data: dict) -> None:
    p = _history_path(vault)
    with p.open("w") as f:
        json.dump(data, f, indent=2)


def record_version(vault: Vault, key: str, value: str) -> None:
    """Append a new version entry for *key* with *value*."""
    if not key:
        raise HistoryError("Key must not be empty.")
    data = _load_history(vault)
    entry = {"value": value, "timestamp": time.time()}
    data.setdefault(key, []).append(entry)
    _save_history(vault, data)


def get_versions(vault: Vault, key: str) -> List[dict]:
    """Return all recorded versions for *key*, oldest first."""
    if not key:
        raise HistoryError("Key must not be empty.")
    data = _load_history(vault)
    return list(data.get(key, []))


def get_latest_version(vault: Vault, key: str) -> Optional[dict]:
    """Return the most recent version entry for *key*, or None."""
    versions = get_versions(vault, key)
    return versions[-1] if versions else None


def clear_history(vault: Vault, key: str) -> int:
    """Remove all history for *key*. Returns number of entries removed."""
    if not key:
        raise HistoryError("Key must not be empty.")
    data = _load_history(vault)
    removed = len(data.pop(key, []))
    _save_history(vault, data)
    return removed
