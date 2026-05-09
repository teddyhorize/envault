"""Copy secrets between vaults or within a vault."""
from __future__ import annotations

from typing import Optional

from envault.vault import Vault, VaultError


class CopyError(Exception):
    """Raised when a copy operation fails."""


def copy_secret(
    src_vault: Vault,
    src_key: str,
    dst_vault: Vault,
    dst_key: Optional[str] = None,
    overwrite: bool = False,
) -> str:
    """Copy a single secret from *src_vault* to *dst_vault*.

    Parameters
    ----------
    src_vault:  Source vault instance.
    src_key:    Key to copy from the source vault.
    dst_vault:  Destination vault instance (may be the same object).
    dst_key:    Key name in the destination vault; defaults to *src_key*.
    overwrite:  When *False* (default) raises :class:`CopyError` if the
                destination key already exists.

    Returns
    -------
    The destination key name.
    """
    if not src_key or not src_key.strip():
        raise CopyError("src_key must not be empty.")

    dst_key = dst_key or src_key
    if not dst_key.strip():
        raise CopyError("dst_key must not be empty.")

    value = src_vault.get(src_key)
    if value is None:
        raise CopyError(f"Key '{src_key}' not found in source vault.")

    if not overwrite and dst_vault.get(dst_key) is not None:
        raise CopyError(
            f"Key '{dst_key}' already exists in destination vault. "
            "Use overwrite=True to replace it."
        )

    dst_vault.set(dst_key, value)
    return dst_key


def copy_all(
    src_vault: Vault,
    dst_vault: Vault,
    overwrite: bool = False,
) -> list[str]:
    """Copy every secret from *src_vault* into *dst_vault*.

    Returns a list of destination key names that were written.
    """
    keys = src_vault.keys()
    if not keys:
        raise CopyError("Source vault is empty — nothing to copy.")

    copied: list[str] = []
    for key in keys:
        copy_secret(src_vault, key, dst_vault, overwrite=overwrite)
        copied.append(key)
    return copied
