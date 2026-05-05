"""Tag management for vault secrets — group and filter secrets by tag."""

from __future__ import annotations

from typing import Dict, List, Optional

from envault.vault import Vault, VaultError

TAGS_META_KEY = "__tags__"


class TagsError(VaultError):
    """Raised when a tag operation fails."""


def _load_tags(vault: Vault) -> Dict[str, List[str]]:
    """Return the internal tag mapping {secret_key: [tag, ...]}."""
    raw = vault.get(TAGS_META_KEY)
    if raw is None:
        return {}
    import json
    try:
        return json.loads(raw)
    except (ValueError, TypeError) as exc:
        raise TagsError("Corrupted tag metadata in vault.") from exc


def _save_tags(vault: Vault, mapping: Dict[str, List[str]]) -> None:
    import json
    vault.set(TAGS_META_KEY, json.dumps(mapping))


def add_tag(vault: Vault, key: str, tag: str) -> None:
    """Add *tag* to the secret identified by *key*."""
    if not key or not key.strip():
        raise TagsError("Secret key must not be empty.")
    if not tag or not tag.strip():
        raise TagsError("Tag must not be empty.")
    if vault.get(key) is None and key != TAGS_META_KEY:
        raise TagsError(f"Secret '{key}' does not exist in the vault.")
    mapping = _load_tags(vault)
    tags = mapping.setdefault(key, [])
    if tag not in tags:
        tags.append(tag)
    _save_tags(vault, mapping)


def remove_tag(vault: Vault, key: str, tag: str) -> bool:
    """Remove *tag* from *key*. Returns True if the tag was present."""
    mapping = _load_tags(vault)
    tags = mapping.get(key, [])
    if tag not in tags:
        return False
    tags.remove(tag)
    if not tags:
        del mapping[key]
    _save_tags(vault, mapping)
    return True


def get_tags(vault: Vault, key: str) -> List[str]:
    """Return the list of tags associated with *key*."""
    return list(_load_tags(vault).get(key, []))


def keys_by_tag(vault: Vault, tag: str) -> List[str]:
    """Return all secret keys that carry *tag*."""
    return [k for k, tags in _load_tags(vault).items() if tag in tags]


def all_tags(vault: Vault) -> Dict[str, List[str]]:
    """Return the full {key: [tags]} mapping (excluding meta key)."""
    return {k: list(v) for k, v in _load_tags(vault).items()}
