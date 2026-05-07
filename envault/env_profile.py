"""Environment profile support: named sets of key filters for different environments (dev, staging, prod)."""

import json
from pathlib import Path
from typing import Dict, List, Optional

PROFILE_FILENAME = ".envault_profiles.json"


class ProfileError(Exception):
    pass


def _profile_path(vault_path: str) -> Path:
    return Path(vault_path).parent / PROFILE_FILENAME


def _load_profiles(vault_path: str) -> Dict[str, List[str]]:
    path = _profile_path(vault_path)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_profiles(vault_path: str, profiles: Dict[str, List[str]]) -> None:
    path = _profile_path(vault_path)
    with open(path, "w") as f:
        json.dump(profiles, f, indent=2)


def define_profile(vault_path: str, name: str, keys: List[str]) -> None:
    """Define or overwrite a named profile with a list of key patterns."""
    if not name or not name.strip():
        raise ProfileError("Profile name must not be empty.")
    if not keys:
        raise ProfileError("Profile must contain at least one key.")
    profiles = _load_profiles(vault_path)
    profiles[name] = list(keys)
    _save_profiles(vault_path, profiles)


def delete_profile(vault_path: str, name: str) -> None:
    """Delete a named profile."""
    profiles = _load_profiles(vault_path)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' does not exist.")
    del profiles[name]
    _save_profiles(vault_path, profiles)


def list_profiles(vault_path: str) -> List[str]:
    """Return all defined profile names."""
    return list(_load_profiles(vault_path).keys())


def get_profile_keys(vault_path: str, name: str) -> List[str]:
    """Return the key list for a named profile."""
    profiles = _load_profiles(vault_path)
    if name not in profiles:
        raise ProfileError(f"Profile '{name}' does not exist.")
    return profiles[name]


def apply_profile(vault_path: str, name: str, vault) -> Dict[str, Optional[str]]:
    """Return a dict of key->value for all keys in the profile that exist in the vault."""
    keys = get_profile_keys(vault_path, name)
    result = {}
    for key in keys:
        value = vault.get(key)
        if value is not None:
            result[key] = value
    return result
