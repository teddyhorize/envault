"""Rename secrets within a vault, with optional bulk rename via prefix substitution."""

from __future__ import annotations

from envault.vault import Vault, VaultError


class RenameError(Exception):
    """Raised when a rename operation fails."""


def rename_secret(vault: Vault, old_key: str, new_key: str, *, overwrite: bool = False) -> None:
    """Rename *old_key* to *new_key* inside *vault*.

    Args:
        vault: Open :class:`~envault.vault.Vault` instance.
        old_key: Existing key name.
        new_key: Desired key name.
        overwrite: If *True*, silently overwrite *new_key* if it already exists.

    Raises:
        RenameError: If *old_key* does not exist, either key is empty, or
            *new_key* already exists and *overwrite* is *False*.
    """
    if not old_key:
        raise RenameError("old_key must not be empty")
    if not new_key:
        raise RenameError("new_key must not be empty")
    if old_key == new_key:
        raise RenameError("old_key and new_key must differ")

    value = vault.get(old_key)
    if value is None:
        raise RenameError(f"Key not found: {old_key!r}")

    if vault.get(new_key) is not None and not overwrite:
        raise RenameError(
            f"Key {new_key!r} already exists. Pass overwrite=True to replace it."
        )

    vault.set(new_key, value)
    vault.delete(old_key)


def rename_prefix(vault: Vault, old_prefix: str, new_prefix: str, *, overwrite: bool = False) -> list[tuple[str, str]]:
    """Rename all keys that start with *old_prefix* by substituting *new_prefix*.

    Returns:
        List of ``(old_key, new_key)`` pairs that were renamed.

    Raises:
        RenameError: If either prefix is empty or no keys match *old_prefix*.
    """
    if not old_prefix:
        raise RenameError("old_prefix must not be empty")
    if not new_prefix:
        raise RenameError("new_prefix must not be empty")

    matching = [k for k in vault.keys() if k.startswith(old_prefix)]
    if not matching:
        raise RenameError(f"No keys found with prefix {old_prefix!r}")

    renamed: list[tuple[str, str]] = []
    for old_key in matching:
        new_key = new_prefix + old_key[len(old_prefix):]
        rename_secret(vault, old_key, new_key, overwrite=overwrite)
        renamed.append((old_key, new_key))

    return renamed
