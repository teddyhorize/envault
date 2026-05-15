"""Time-to-live (TTL) management for vault secrets."""

import json
import time
from pathlib import Path
from typing import Optional

from envault.vault import Vault, VaultError


class TTLError(Exception):
    """Raised when a TTL operation fails."""


def _ttl_path(vault: Vault) -> Path:
    return Path(vault.path).with_suffix(".ttl.json")


def _load_ttl(vault: Vault) -> dict:
    p = _ttl_path(vault)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise TTLError(f"Failed to load TTL data: {exc}") from exc


def _save_ttl(vault: Vault, data: dict) -> None:
    try:
        _ttl_path(vault).write_text(json.dumps(data, indent=2))
    except OSError as exc:
        raise TTLError(f"Failed to save TTL data: {exc}") from exc


def set_ttl(vault: Vault, key: str, seconds: int) -> float:
    """Set a TTL for *key*; returns the absolute expiry timestamp."""
    if not key:
        raise TTLError("Key must not be empty.")
    if vault.get(key) is None:
        raise TTLError(f"Key '{key}' does not exist in the vault.")
    if seconds <= 0:
        raise TTLError("TTL must be a positive number of seconds.")
    expiry = time.time() + seconds
    data = _load_ttl(vault)
    data[key] = {"expires_at": expiry, "ttl_seconds": seconds}
    _save_ttl(vault, data)
    return expiry


def get_ttl(vault: Vault, key: str) -> Optional[dict]:
    """Return TTL info for *key*, or None if no TTL is set."""
    if not key:
        raise TTLError("Key must not be empty.")
    return _load_ttl(vault).get(key)


def is_expired(vault: Vault, key: str) -> bool:
    """Return True if *key* has a TTL that has elapsed."""
    info = get_ttl(vault, key)
    if info is None:
        return False
    return time.time() >= info["expires_at"]


def clear_ttl(vault: Vault, key: str) -> bool:
    """Remove the TTL for *key*. Returns True if a TTL was present."""
    if not key:
        raise TTLError("Key must not be empty.")
    data = _load_ttl(vault)
    if key not in data:
        return False
    del data[key]
    _save_ttl(vault, data)
    return True


def list_ttl(vault: Vault) -> dict:
    """Return all TTL entries for the vault."""
    return _load_ttl(vault)


def purge_expired(vault: Vault) -> list:
    """Delete all expired keys from the vault and clear their TTLs."""
    data = _load_ttl(vault)
    now = time.time()
    purged = []
    for key, info in list(data.items()):
        if now >= info["expires_at"]:
            try:
                vault.delete(key)
            except VaultError:
                pass
            del data[key]
            purged.append(key)
    _save_ttl(vault, data)
    return purged
