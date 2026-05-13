"""Secret description/documentation management for envault vaults."""

import json
from pathlib import Path
from envault.vault import Vault


class DescriptionError(Exception):
    pass


def _description_path(vault: Vault) -> Path:
    return Path(vault.path).with_suffix(".descriptions.json")


def _load_descriptions(vault: Vault) -> dict:
    path = _description_path(vault)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_descriptions(vault: Vault, data: dict) -> None:
    path = _description_path(vault)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def set_description(vault: Vault, key: str, description: str) -> None:
    """Set a human-readable description for a secret key."""
    if not key:
        raise DescriptionError("Key must not be empty.")
    if vault.get(key) is None:
        raise DescriptionError(f"Key '{key}' does not exist in the vault.")
    if not isinstance(description, str):
        raise DescriptionError("Description must be a string.")
    data = _load_descriptions(vault)
    data[key] = description.strip()
    _save_descriptions(vault, data)


def get_description(vault: Vault, key: str) -> str | None:
    """Return the description for a key, or None if not set."""
    if not key:
        raise DescriptionError("Key must not be empty.")
    data = _load_descriptions(vault)
    return data.get(key)


def remove_description(vault: Vault, key: str) -> bool:
    """Remove the description for a key. Returns True if it existed."""
    if not key:
        raise DescriptionError("Key must not be empty.")
    data = _load_descriptions(vault)
    if key not in data:
        return False
    del data[key]
    _save_descriptions(vault, data)
    return True


def list_descriptions(vault: Vault) -> dict:
    """Return all key->description mappings for this vault."""
    return dict(_load_descriptions(vault))
