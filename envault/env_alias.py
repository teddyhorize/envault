"""Secret aliasing: create named aliases that point to existing vault keys."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class AliasError(Exception):
    """Raised when an alias operation fails."""


def _alias_path(vault: Vault) -> Path:
    return Path(vault.path).with_suffix(".aliases.json")


def _load_aliases(vault: Vault) -> Dict[str, str]:
    path = _alias_path(vault)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise AliasError(f"Failed to load aliases: {exc}") from exc


def _save_aliases(vault: Vault, aliases: Dict[str, str]) -> None:
    path = _alias_path(vault)
    try:
        path.write_text(json.dumps(aliases, indent=2))
    except OSError as exc:
        raise AliasError(f"Failed to save aliases: {exc}") from exc


def add_alias(vault: Vault, alias: str, target_key: str) -> None:
    """Create *alias* pointing to *target_key*. Target must exist in vault."""
    if not alias or not alias.strip():
        raise AliasError("Alias name must not be empty.")
    if not target_key or not target_key.strip():
        raise AliasError("Target key must not be empty.")
    if vault.get(target_key) is None:
        raise AliasError(f"Target key '{target_key}' does not exist in vault.")
    aliases = _load_aliases(vault)
    aliases[alias] = target_key
    _save_aliases(vault, aliases)


def remove_alias(vault: Vault, alias: str) -> None:
    """Remove an existing alias."""
    aliases = _load_aliases(vault)
    if alias not in aliases:
        raise AliasError(f"Alias '{alias}' does not exist.")
    del aliases[alias]
    _save_aliases(vault, aliases)


def resolve_alias(vault: Vault, alias: str) -> Optional[str]:
    """Return the value of the secret that *alias* points to, or None."""
    aliases = _load_aliases(vault)
    target_key = aliases.get(alias)
    if target_key is None:
        return None
    return vault.get(target_key)


def list_aliases(vault: Vault) -> Dict[str, str]:
    """Return mapping of alias -> target_key."""
    return dict(_load_aliases(vault))
