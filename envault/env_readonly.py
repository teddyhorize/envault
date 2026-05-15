"""Read-only protection for vault secrets."""

import json
from pathlib import Path
from envault.vault import Vault


class ReadOnlyError(Exception):
    pass


def _readonly_path(vault: Vault) -> Path:
    return Path(vault.path).parent / (Path(vault.path).stem + ".readonly.json")


def _load_readonly(vault: Vault) -> set:
    p = _readonly_path(vault)
    if not p.exists():
        return set()
    return set(json.loads(p.read_text()))


def _save_readonly(vault: Vault, keys: set) -> None:
    _readonly_path(vault).write_text(json.dumps(sorted(keys)))


def protect(vault: Vault, key: str) -> None:
    """Mark a secret as read-only (protected from modification)."""
    if not key:
        raise ReadOnlyError("Key must not be empty.")
    if vault.get(key) is None:
        raise ReadOnlyError(f"Key '{key}' does not exist in vault.")
    keys = _load_readonly(vault)
    keys.add(key)
    _save_readonly(vault, keys)


def unprotect(vault: Vault, key: str) -> None:
    """Remove read-only protection from a secret."""
    if not key:
        raise ReadOnlyError("Key must not be empty.")
    keys = _load_readonly(vault)
    keys.discard(key)
    _save_readonly(vault, keys)


def is_protected(vault: Vault, key: str) -> bool:
    """Return True if the key is marked as read-only."""
    return key in _load_readonly(vault)


def list_protected(vault: Vault) -> list:
    """Return a sorted list of all read-only protected keys."""
    return sorted(_load_readonly(vault))


def assert_writable(vault: Vault, key: str) -> None:
    """Raise ReadOnlyError if the key is protected."""
    if is_protected(vault, key):
        raise ReadOnlyError(f"Key '{key}' is read-only and cannot be modified.")
