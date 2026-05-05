"""Secret rotation support for envault vaults."""

import time
from typing import Optional
from envault.vault import Vault, VaultError
from envault.audit import AuditLog


class RotationError(Exception):
    """Raised when a secret rotation operation fails."""


def rotate_secret(
    vault: Vault,
    key: str,
    new_value: str,
    audit_log: Optional[AuditLog] = None,
) -> str:
    """Replace the value of an existing secret and return the old value.

    Args:
        vault: The Vault instance to operate on.
        key: The secret key to rotate.
        new_value: The new plaintext value to store.
        audit_log: Optional AuditLog to record the rotation event.

    Returns:
        The previous plaintext value of the secret.

    Raises:
        RotationError: If the key does not exist or new_value is empty.
    """
    if not key:
        raise RotationError("Key must not be empty.")
    if not new_value:
        raise RotationError("New value must not be empty.")

    old_value = vault.get(key)
    if old_value is None:
        raise RotationError(f"Key '{key}' not found; cannot rotate a non-existent secret.")

    vault.set(key, new_value)

    if audit_log is not None:
        audit_log.record(
            action="rotate",
            key=key,
            detail=f"secret rotated at {int(time.time())}",
        )

    return old_value


def rotate_all(
    vault: Vault,
    new_values: dict,
    audit_log: Optional[AuditLog] = None,
) -> dict:
    """Rotate multiple secrets at once.

    Args:
        vault: The Vault instance to operate on.
        new_values: Mapping of key -> new_value pairs.
        audit_log: Optional AuditLog to record each rotation.

    Returns:
        Dict mapping each key to its previous value.

    Raises:
        RotationError: If any key is missing or a value is empty.
    """
    if not new_values:
        raise RotationError("new_values mapping must not be empty.")

    previous = {}
    for key, new_value in new_values.items():
        previous[key] = rotate_secret(vault, key, new_value, audit_log=audit_log)
    return previous
