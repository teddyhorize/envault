"""Compare two vault files and report key-level differences with value previews."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from envault.vault import Vault, VaultError


class CompareError(Exception):
    """Raised when a vault comparison fails."""


@dataclass
class CompareResult:
    only_in_left: List[str] = field(default_factory=list)
    only_in_right: List[str] = field(default_factory=list)
    changed: List[str] = field(default_factory=list)
    identical: List[str] = field(default_factory=list)

    @property
    def has_differences(self) -> bool:
        return bool(self.only_in_left or self.only_in_right or self.changed)

    def summary(self) -> str:
        lines = []
        for key in sorted(self.only_in_left):
            lines.append(f"  < {key}  (only in left)")
        for key in sorted(self.only_in_right):
            lines.append(f"  > {key}  (only in right)")
        for key in sorted(self.changed):
            lines.append(f"  ~ {key}  (value differs)")
        if not lines:
            return "Vaults are identical."
        return "\n".join(lines)


def _preview(value: str, max_len: int = 8) -> str:
    """Return a short masked preview of a secret value."""
    if len(value) <= max_len:
        return "*" * len(value)
    return value[:2] + "***" + value[-1]


def compare_vaults(
    left: Vault,
    left_password: str,
    right: Vault,
    right_password: str,
    reveal: bool = False,
) -> CompareResult:
    """Compare two vaults key-by-key and return a CompareResult."""
    try:
        left_keys = set(left.list_keys())
    except VaultError as exc:
        raise CompareError(f"Cannot read left vault: {exc}") from exc

    try:
        right_keys = set(right.list_keys())
    except VaultError as exc:
        raise CompareError(f"Cannot read right vault: {exc}") from exc

    result = CompareResult()
    result.only_in_left = sorted(left_keys - right_keys)
    result.only_in_right = sorted(right_keys - left_keys)

    for key in sorted(left_keys & right_keys):
        lv = left.get(key, left_password)
        rv = right.get(key, right_password)
        if lv == rv:
            result.identical.append(key)
        else:
            result.changed.append(key)

    return result
