"""Clone (deep-copy) secrets from one vault to another, with optional key filtering."""

from __future__ import annotations

from typing import List, Optional

from envault.vault import Vault, VaultError


class CloneError(Exception):
    """Raised when a clone operation fails."""


def clone_vault(
    src: Vault,
    src_password: str,
    dst: Vault,
    dst_password: str,
    keys: Optional[List[str]] = None,
    overwrite: bool = True,
) -> List[str]:
    """Copy secrets from *src* into *dst*.

    Parameters
    ----------
    src:          Source vault instance.
    src_password: Master password for the source vault.
    dst:          Destination vault instance.
    dst_password: Master password for the destination vault.
    keys:         Explicit list of keys to clone.  ``None`` means all keys.
    overwrite:    When *False*, skip keys that already exist in *dst*.

    Returns
    -------
    List of key names that were actually written.
    """
    try:
        all_keys: List[str] = src.list_keys()
    except VaultError as exc:
        raise CloneError(f"Cannot read source vault: {exc}") from exc

    if not all_keys:
        raise CloneError("Source vault is empty – nothing to clone.")

    target_keys = keys if keys is not None else all_keys

    # Validate requested keys exist in source
    missing = [k for k in target_keys if k not in all_keys]
    if missing:
        raise CloneError(f"Keys not found in source vault: {missing}")

    written: List[str] = []
    for key in target_keys:
        if not overwrite and dst.get(key, dst_password) is not None:
            continue
        value = src.get(key, src_password)
        if value is None:
            continue
        dst.set(key, value, dst_password)
        written.append(key)

    return written
