"""Namespace support for grouping secrets by prefix."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class NamespaceError(Exception):
    """Raised when a namespace operation fails."""


def _namespace_path(vault: Vault) -> Path:
    return Path(vault.path).with_suffix(".namespaces.json")


def _load_namespaces(vault: Vault) -> Dict[str, str]:
    """Load namespace -> description mapping from disk."""
    p = _namespace_path(vault)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise NamespaceError(f"Failed to load namespaces: {exc}") from exc


def _save_namespaces(vault: Vault, data: Dict[str, str]) -> None:
    p = _namespace_path(vault)
    try:
        p.write_text(json.dumps(data, indent=2))
    except OSError as exc:
        raise NamespaceError(f"Failed to save namespaces: {exc}") from exc


def define_namespace(vault: Vault, namespace: str, description: str = "") -> None:
    """Register a namespace with an optional description."""
    if not namespace:
        raise NamespaceError("Namespace name must not be empty.")
    if not namespace.isidentifier() and not all(c.isalnum() or c == "_" for c in namespace):
        raise NamespaceError(f"Invalid namespace name: {namespace!r}")
    data = _load_namespaces(vault)
    data[namespace] = description
    _save_namespaces(vault, data)


def list_namespaces(vault: Vault) -> Dict[str, str]:
    """Return all defined namespaces and their descriptions."""
    return _load_namespaces(vault)


def delete_namespace(vault: Vault, namespace: str) -> None:
    """Remove a namespace definition (does not delete secrets)."""
    if not namespace:
        raise NamespaceError("Namespace name must not be empty.")
    data = _load_namespaces(vault)
    if namespace not in data:
        raise NamespaceError(f"Namespace {namespace!r} does not exist.")
    del data[namespace]
    _save_namespaces(vault, data)


def get_secrets_in_namespace(vault: Vault, namespace: str) -> Dict[str, Optional[str]]:
    """Return all secrets whose keys start with '<namespace>_' or '<namespace>/'."""
    if not namespace:
        raise NamespaceError("Namespace name must not be empty.")
    prefixes = (f"{namespace}_", f"{namespace}/")
    all_keys: List[str] = vault.list()
    result: Dict[str, Optional[str]] = {}
    for key in all_keys:
        if any(key.startswith(p) for p in prefixes):
            result[key] = vault.get(key)
    return result
