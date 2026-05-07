"""Merge two vaults or env files into a target vault with conflict resolution."""
from __future__ import annotations

from enum import Enum
from typing import Dict, List, NamedTuple, Optional

from envault.vault import Vault, VaultError


class MergeError(Exception):
    """Raised when a merge operation fails."""


class ConflictStrategy(str, Enum):
    KEEP_LEFT = "keep_left"   # keep existing (destination) value
    KEEP_RIGHT = "keep_right" # overwrite with source value
    FAIL = "fail"             # raise MergeError on conflict


class MergeResult(NamedTuple):
    added: List[str]
    updated: List[str]
    skipped: List[str]
    conflicts: List[str]

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0

    def summary(self) -> str:
        lines = [
            f"Added   : {len(self.added)}",
            f"Updated : {len(self.updated)}",
            f"Skipped : {len(self.skipped)}",
            f"Conflicts: {len(self.conflicts)}",
        ]
        return "\n".join(lines)


def merge_dicts(
    source: Dict[str, str],
    destination: Dict[str, str],
    strategy: ConflictStrategy = ConflictStrategy.KEEP_RIGHT,
) -> tuple[Dict[str, str], MergeResult]:
    """Merge two plain dictionaries with the same conflict resolution logic.

    This is useful when working with env files loaded into memory rather than
    Vault objects.  The *destination* dict is not mutated; a new merged dict
    is returned alongside the MergeResult.

    Args:
        source: Dictionary to read values from.
        destination: Dictionary to merge values into (not mutated).
        strategy: How to handle keys that exist in both dicts.

    Returns:
        A tuple of (merged_dict, MergeResult).

    Raises:
        MergeError: If strategy is FAIL and a conflict is detected.
    """
    merged = dict(destination)
    added: List[str] = []
    updated: List[str] = []
    skipped: List[str] = []
    conflicts: List[str] = []

    for key, src_value in source.items():
        if key in destination:
            conflicts.append(key)
            if strategy == ConflictStrategy.FAIL:
                raise MergeError(
                    f"Conflict on key '{key}' and strategy is FAIL."
                )
            elif strategy == ConflictStrategy.KEEP_RIGHT:
                merged[key] = src_value
                updated.append(key)
            else:  # KEEP_LEFT
                skipped.append(key)
        else:
            merged[key] = src_value
            added.append(key)

    return merged, MergeResult(
        added=added,
        updated=updated,
        skipped=skipped,
        conflicts=conflicts,
    )


def merge_vaults(
    source: Vault,
    destination: Vault,
    strategy: ConflictStrategy = ConflictStrategy.KEEP_RIGHT,
    keys: Optional[List[str]] = None,
) -> MergeResult:
    """Merge secrets from *source* into *destination*.

    Args:
        source: Vault to read values from.
        destination: Vault to write values into.
        strategy: How to handle keys that exist in both vaults.
        keys: Optional explicit list of keys to merge; merges all if None.

    Returns:
        A MergeResult describing what happened.

    Raises:
        MergeError: If strategy is FAIL and a conflict is detected, or if
                    either vault cannot be read.
    """
    try:
        src_keys: List[str] = keys if keys is not None else source.keys()
    except VaultError as exc:
        raise MergeError(f"Cannot read source vault: {exc}") from exc

    added: List[str] = []
    updated: List[str] = []
    skipped: List[str] = []
    conflicts: List[str] = []

    for key in src_keys:
        src_value = source.get(key)
        if src_value is None:
            skipped.append(key)
            continue

        dst_value = destination.get(key)
        if dst_value is None:
            destination.set(key, src_value)
            added.append(key)
        else:
            # Conflict: key exists in both vaults
            conflicts.append(key)
            if strategy == ConflictStrategy.FAIL:
                raise MergeError(
                    f"Conflict on key '{key}' and strategy is FAIL."
                )
            elif strategy == ConflictStrategy.KEEP_RIGHT:
                destination.set(key, src_value)
                updated.append(key)
            else:  # KEEP_LEFT
                skipped.append(key)

    return MergeResult(
        added=added,
        updated=updated,
        skipped=skipped,
        conflicts=conflicts,
    )
