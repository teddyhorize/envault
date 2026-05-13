"""Secret dependency tracking for envault vaults."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class DependencyError(Exception):
    """Raised when a dependency operation fails."""


def _dep_path(vault: Vault) -> Path:
    return Path(vault.path).with_suffix(".deps.json")


def _load_deps(vault: Vault) -> Dict[str, List[str]]:
    p = _dep_path(vault)
    if not p.exists():
        return {}
    with open(p) as f:
        return json.load(f)


def _save_deps(vault: Vault, deps: Dict[str, List[str]]) -> None:
    with open(_dep_path(vault), "w") as f:
        json.dump(deps, f, indent=2)


def add_dependency(vault: Vault, key: str, depends_on: str) -> None:
    """Record that *key* depends on *depends_on*."""
    if not key:
        raise DependencyError("key must not be empty")
    if not depends_on:
        raise DependencyError("depends_on must not be empty")
    if vault.get(key) is None:
        raise DependencyError(f"key '{key}' not found in vault")
    if vault.get(depends_on) is None:
        raise DependencyError(f"depends_on key '{depends_on}' not found in vault")
    if key == depends_on:
        raise DependencyError("a key cannot depend on itself")
    deps = _load_deps(vault)
    existing = deps.get(key, [])
    if depends_on not in existing:
        existing.append(depends_on)
    deps[key] = existing
    _save_deps(vault, deps)


def remove_dependency(vault: Vault, key: str, depends_on: str) -> None:
    """Remove the dependency of *key* on *depends_on*."""
    deps = _load_deps(vault)
    existing = deps.get(key, [])
    if depends_on not in existing:
        raise DependencyError(f"no dependency '{depends_on}' found for key '{key}'")
    existing.remove(depends_on)
    if existing:
        deps[key] = existing
    else:
        deps.pop(key, None)
    _save_deps(vault, deps)


def get_dependencies(vault: Vault, key: str) -> List[str]:
    """Return the list of keys that *key* depends on."""
    deps = _load_deps(vault)
    return deps.get(key, [])


def get_dependents(vault: Vault, key: str) -> List[str]:
    """Return keys that depend on *key* (reverse lookup)."""
    deps = _load_deps(vault)
    return [k for k, v in deps.items() if key in v]


def list_all_dependencies(vault: Vault) -> Dict[str, List[str]]:
    """Return the full dependency map for the vault."""
    return dict(_load_deps(vault))
