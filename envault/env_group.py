"""Group management for envault: define named groups of secrets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class GroupError(Exception):
    """Raised when a group operation fails."""


def _group_path(vault: Vault) -> Path:
    return Path(vault.path).with_suffix(".groups.json")


def _load_groups(vault: Vault) -> Dict[str, List[str]]:
    path = _group_path(vault)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_groups(vault: Vault, groups: Dict[str, List[str]]) -> None:
    path = _group_path(vault)
    with open(path, "w") as f:
        json.dump(groups, f, indent=2)


def define_group(vault: Vault, name: str, keys: List[str]) -> None:
    """Define a named group of secret keys."""
    if not name:
        raise GroupError("Group name must not be empty.")
    if not keys:
        raise GroupError("Group must contain at least one key.")
    for key in keys:
        if vault.get(key) is None:
            raise GroupError(f"Key '{key}' does not exist in the vault.")
    groups = _load_groups(vault)
    groups[name] = list(keys)
    _save_groups(vault, groups)


def delete_group(vault: Vault, name: str) -> None:
    """Delete a named group."""
    groups = _load_groups(vault)
    if name not in groups:
        raise GroupError(f"Group '{name}' does not exist.")
    del groups[name]
    _save_groups(vault, groups)


def list_groups(vault: Vault) -> Dict[str, List[str]]:
    """Return all defined groups."""
    return _load_groups(vault)


def get_group(vault: Vault, name: str) -> Optional[List[str]]:
    """Return the keys in a group, or None if it doesn't exist."""
    return _load_groups(vault).get(name)


def resolve_group(vault: Vault, name: str) -> Dict[str, str]:
    """Return a dict of key->value for all keys in the group."""
    keys = get_group(vault, name)
    if keys is None:
        raise GroupError(f"Group '{name}' does not exist.")
    result = {}
    for key in keys:
        value = vault.get(key)
        if value is None:
            raise GroupError(f"Key '{key}' in group '{name}' no longer exists in the vault.")
        result[key] = value
    return result
