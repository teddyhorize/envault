"""Role-based access control for vault keys."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

ACCESS_FILE = ".envault_access.json"

ROLES = {"reader", "writer", "admin"}


class AccessControlError(Exception):
    """Raised when an access control operation fails."""


def _access_path(vault_path: str) -> Path:
    return Path(vault_path).parent / ACCESS_FILE


def _load_acl(vault_path: str) -> Dict[str, List[str]]:
    path = _access_path(vault_path)
    if not path.exists():
        return {}
    with open(path, "r") as f:
        return json.load(f)


def _save_acl(vault_path: str, acl: Dict[str, List[str]]) -> None:
    path = _access_path(vault_path)
    with open(path, "w") as f:
        json.dump(acl, f, indent=2)


def grant_access(vault_path: str, user: str, role: str) -> None:
    """Grant a role to a user for the given vault."""
    if not user or not user.strip():
        raise AccessControlError("User name must not be empty.")
    if role not in ROLES:
        raise AccessControlError(f"Invalid role '{role}'. Must be one of: {sorted(ROLES)}.")
    acl = _load_acl(vault_path)
    acl.setdefault(user, [])
    if role not in acl[user]:
        acl[user].append(role)
    _save_acl(vault_path, acl)


def revoke_access(vault_path: str, user: str, role: Optional[str] = None) -> None:
    """Revoke a role (or all roles) from a user."""
    if not user or not user.strip():
        raise AccessControlError("User name must not be empty.")
    acl = _load_acl(vault_path)
    if user not in acl:
        raise AccessControlError(f"User '{user}' has no access entries.")
    if role is None:
        del acl[user]
    else:
        if role not in ROLES:
            raise AccessControlError(f"Invalid role '{role}'. Must be one of: {sorted(ROLES)}.")
        if role not in acl[user]:
            raise AccessControlError(f"User '{user}' does not have role '{role}'.")
        acl[user].remove(role)
        if not acl[user]:
            del acl[user]
    _save_acl(vault_path, acl)


def get_roles(vault_path: str, user: str) -> List[str]:
    """Return the list of roles assigned to a user."""
    acl = _load_acl(vault_path)
    return list(acl.get(user, []))


def list_access(vault_path: str) -> Dict[str, List[str]]:
    """Return the full ACL mapping for the vault."""
    return _load_acl(vault_path)


def has_role(vault_path: str, user: str, role: str) -> bool:
    """Return True if the user has the specified role."""
    return role in get_roles(vault_path, user)
