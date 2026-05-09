"""Secret pinning: mark secrets as pinned to prevent accidental overwrite or deletion."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from envault.vault import Vault, VaultError


class PinError(Exception):
    pass


def _pin_path(vault: Vault) -> Path:
    return Path(vault.path).parent / (Path(vault.path).stem + ".pins.json")


def _load_pins(vault: Vault) -> dict:
    p = _pin_path(vault)
    if not p.exists():
        return {"pinned": []}
    with open(p, "r") as f:
        return json.load(f)


def _save_pins(vault: Vault, data: dict) -> None:
    p = _pin_path(vault)
    with open(p, "w") as f:
        json.dump(data, f, indent=2)


def pin_secret(vault: Vault, key: str) -> None:
    """Mark a secret key as pinned."""
    if not key:
        raise PinError("Key must not be empty.")
    if vault.get(key) is None:
        raise PinError(f"Key '{key}' does not exist in vault.")
    data = _load_pins(vault)
    if key not in data["pinned"]:
        data["pinned"].append(key)
        _save_pins(vault, data)


def unpin_secret(vault: Vault, key: str) -> None:
    """Remove the pin from a secret key."""
    if not key:
        raise PinError("Key must not be empty.")
    data = _load_pins(vault)
    if key in data["pinned"]:
        data["pinned"].remove(key)
        _save_pins(vault, data)


def is_pinned(vault: Vault, key: str) -> bool:
    """Return True if the key is pinned."""
    data = _load_pins(vault)
    return key in data["pinned"]


def list_pinned(vault: Vault) -> List[str]:
    """Return a list of all pinned keys."""
    data = _load_pins(vault)
    return list(data["pinned"])


def assert_not_pinned(vault: Vault, key: str, operation: str = "modify") -> None:
    """Raise PinError if the key is pinned, blocking the operation."""
    if is_pinned(vault, key):
        raise PinError(f"Key '{key}' is pinned and cannot be {operation}d. Unpin it first.")
