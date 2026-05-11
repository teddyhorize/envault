"""Annotation support for vault secrets — attach human-readable descriptions to keys."""

import json
from pathlib import Path
from envault.vault import Vault, VaultError


class AnnotateError(Exception):
    pass


def _annotation_path(vault: Vault) -> Path:
    return Path(vault.path).with_suffix(".annotations.json")


def _load_annotations(vault: Vault) -> dict:
    p = _annotation_path(vault)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError) as e:
        raise AnnotateError(f"Failed to load annotations: {e}") from e


def _save_annotations(vault: Vault, data: dict) -> None:
    p = _annotation_path(vault)
    try:
        p.write_text(json.dumps(data, indent=2))
    except OSError as e:
        raise AnnotateError(f"Failed to save annotations: {e}") from e


def set_annotation(vault: Vault, key: str, description: str) -> None:
    """Attach a description to a vault key."""
    if not key:
        raise AnnotateError("Key must not be empty.")
    if vault.get(key) is None:
        raise AnnotateError(f"Key '{key}' does not exist in the vault.")
    data = _load_annotations(vault)
    data[key] = description
    _save_annotations(vault, data)


def get_annotation(vault: Vault, key: str) -> str | None:
    """Return the description for a key, or None if not set."""
    if not key:
        raise AnnotateError("Key must not be empty.")
    data = _load_annotations(vault)
    return data.get(key)


def remove_annotation(vault: Vault, key: str) -> bool:
    """Remove the annotation for a key. Returns True if removed, False if not found."""
    if not key:
        raise AnnotateError("Key must not be empty.")
    data = _load_annotations(vault)
    if key not in data:
        return False
    del data[key]
    _save_annotations(vault, data)
    return True


def list_annotations(vault: Vault) -> dict:
    """Return all key→description mappings."""
    return dict(_load_annotations(vault))
