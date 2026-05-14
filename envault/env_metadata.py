"""Attach arbitrary metadata key-value pairs to vault secrets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

from envault.vault import Vault, VaultError


class MetadataError(Exception):
    """Raised when a metadata operation fails."""


def _metadata_path(vault: Vault) -> Path:
    return Path(vault.path).with_suffix(".metadata.json")


def _load_metadata(vault: Vault) -> Dict[str, Dict[str, str]]:
    path = _metadata_path(vault)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise MetadataError(f"Failed to load metadata: {exc}") from exc


def _save_metadata(vault: Vault, data: Dict[str, Dict[str, str]]) -> None:
    path = _metadata_path(vault)
    try:
        path.write_text(json.dumps(data, indent=2))
    except OSError as exc:
        raise MetadataError(f"Failed to save metadata: {exc}") from exc


def set_metadata(vault: Vault, key: str, field: str, value: str) -> None:
    """Attach a metadata field to a vault secret key."""
    if not key:
        raise MetadataError("Secret key must not be empty.")
    if not field:
        raise MetadataError("Metadata field name must not be empty.")
    if vault.get(key) is None:
        raise MetadataError(f"Secret '{key}' does not exist in the vault.")
    data = _load_metadata(vault)
    data.setdefault(key, {})[field] = value
    _save_metadata(vault, data)


def get_metadata(vault: Vault, key: str, field: str) -> Optional[str]:
    """Return the metadata value for a field on a secret, or None."""
    data = _load_metadata(vault)
    return data.get(key, {}).get(field)


def get_all_metadata(vault: Vault, key: str) -> Dict[str, str]:
    """Return all metadata fields for a secret as a dict."""
    data = _load_metadata(vault)
    return dict(data.get(key, {}))


def remove_metadata(vault: Vault, key: str, field: str) -> bool:
    """Remove a metadata field from a secret. Returns True if it existed."""
    data = _load_metadata(vault)
    if key in data and field in data[key]:
        del data[key][field]
        if not data[key]:
            del data[key]
        _save_metadata(vault, data)
        return True
    return False


def clear_metadata(vault: Vault, key: str) -> None:
    """Remove all metadata for a secret."""
    data = _load_metadata(vault)
    if key in data:
        del data[key]
        _save_metadata(vault, data)
