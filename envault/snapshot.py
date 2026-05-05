"""Vault snapshot and restore functionality for envault."""

from __future__ import annotations

import json
import time
from typing import Dict, Any

from envault.vault import Vault, VaultError


class SnapshotError(Exception):
    """Raised when a snapshot operation fails."""


def create_snapshot(vault: Vault) -> str:
    """Serialize the current vault contents into a JSON snapshot string.

    Args:
        vault: An open, unlocked Vault instance.

    Returns:
        A JSON string representing the snapshot.

    Raises:
        SnapshotError: If the vault has no secrets to snapshot.
    """
    keys = vault.list_keys()
    if not keys:
        raise SnapshotError("Cannot snapshot an empty vault.")

    secrets: Dict[str, str] = {}
    for key in keys:
        value = vault.get(key)
        if value is not None:
            secrets[key] = value

    payload: Dict[str, Any] = {
        "created_at": time.time(),
        "secrets": secrets,
    }
    return json.dumps(payload)


def restore_snapshot(vault: Vault, snapshot_json: str, overwrite: bool = False) -> int:
    """Restore secrets from a JSON snapshot into a vault.

    Args:
        vault: The target Vault instance.
        snapshot_json: A snapshot string produced by :func:`create_snapshot`.
        overwrite: If True, existing keys will be overwritten; otherwise they
                   are skipped.

    Returns:
        The number of secrets actually written.

    Raises:
        SnapshotError: If the snapshot JSON is invalid or missing required fields.
    """
    try:
        payload = json.loads(snapshot_json)
        secrets: Dict[str, str] = payload["secrets"]
    except (json.JSONDecodeError, KeyError) as exc:
        raise SnapshotError(f"Invalid snapshot data: {exc}") from exc

    written = 0
    for key, value in secrets.items():
        if not overwrite and vault.get(key) is not None:
            continue
        try:
            vault.set(key, value)
            written += 1
        except VaultError as exc:
            raise SnapshotError(f"Failed to restore key '{key}': {exc}") from exc

    return written
