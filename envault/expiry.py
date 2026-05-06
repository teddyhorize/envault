"""Secret expiry management for envault vaults."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError

_EXPIRY_SUFFIX = ".expiry.json"


class ExpiryError(Exception):
    """Raised when an expiry operation fails."""


def _expiry_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix("") .parent / (Path(vault_path).stem + _EXPIRY_SUFFIX)


def _load_expiry(vault_path: str) -> Dict[str, float]:
    path = _expiry_path(vault_path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise ExpiryError(f"Failed to load expiry data: {exc}") from exc


def _save_expiry(vault_path: str, data: Dict[str, float]) -> None:
    path = _expiry_path(vault_path)
    try:
        path.write_text(json.dumps(data, indent=2))
    except OSError as exc:
        raise ExpiryError(f"Failed to save expiry data: {exc}") from exc


def set_expiry(vault: Vault, key: str, ttl_seconds: float) -> float:
    """Set a TTL (in seconds) for *key*. Returns the absolute expiry timestamp."""
    if not key:
        raise ExpiryError("Key must not be empty.")
    if vault.get(key) is None:
        raise ExpiryError(f"Key '{key}' does not exist in the vault.")
    if ttl_seconds <= 0:
        raise ExpiryError("TTL must be a positive number of seconds.")
    expires_at = time.time() + ttl_seconds
    data = _load_expiry(vault.path)
    data[key] = expires_at
    _save_expiry(vault.path, data)
    return expires_at


def get_expiry(vault: Vault, key: str) -> Optional[float]:
    """Return the expiry timestamp for *key*, or None if no expiry is set."""
    data = _load_expiry(vault.path)
    return data.get(key)


def is_expired(vault: Vault, key: str) -> bool:
    """Return True if *key* has passed its expiry time."""
    expires_at = get_expiry(vault, key)
    if expires_at is None:
        return False
    return time.time() > expires_at


def purge_expired(vault: Vault, password: str) -> List[str]:
    """Delete all expired secrets from *vault*. Returns list of purged keys."""
    data = _load_expiry(vault.path)
    now = time.time()
    purged: List[str] = []
    for key, expires_at in list(data.items()):
        if now > expires_at:
            try:
                vault.delete(key)
            except VaultError:
                pass
            del data[key]
            purged.append(key)
    _save_expiry(vault.path, data)
    return purged
