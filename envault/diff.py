"""Vault diff module: compare secrets between two vault files."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from envault.vault import Vault, VaultError


class DiffError(Exception):
    """Raised when a diff operation fails."""


@dataclass
class DiffResult:
    """Holds the result of comparing two vaults."""

    added: List[str] = field(default_factory=list)       # keys only in right
    removed: List[str] = field(default_factory=list)     # keys only in left
    changed: List[str] = field(default_factory=list)     # keys in both but values differ
    unchanged: List[str] = field(default_factory=list)   # keys in both with same values

    @property
    def has_differences(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        lines = []
        for key in sorted(self.added):
            lines.append(f"+ {key}")
        for key in sorted(self.removed):
            lines.append(f"- {key}")
        for key in sorted(self.changed):
            lines.append(f"~ {key}")
        for key in sorted(self.unchanged):
            lines.append(f"  {key}")
        return "\n".join(lines) if lines else "(no secrets)"


def diff_vaults(left: Vault, left_password: str,
               right: Vault, right_password: str) -> DiffResult:
    """Compare secrets in two vaults, decrypting with their respective passwords."""
    try:
        left_keys = set(left.keys())
    except VaultError as exc:
        raise DiffError(f"Failed to read left vault: {exc}") from exc

    try:
        right_keys = set(right.keys())
    except VaultError as exc:
        raise DiffError(f"Failed to read right vault: {exc}") from exc

    result = DiffResult()
    result.added = list(right_keys - left_keys)
    result.removed = list(left_keys - right_keys)

    for key in left_keys & right_keys:
        try:
            lv = left.get(key, left_password)
            rv = right.get(key, right_password)
        except VaultError as exc:
            raise DiffError(f"Failed to decrypt key '{key}': {exc}") from exc
        if lv == rv:
            result.unchanged.append(key)
        else:
            result.changed.append(key)

    return result
