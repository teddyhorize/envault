"""Checksum utilities for detecting vault tampering or drift."""

import hashlib
import json
from typing import Dict, Optional

from envault.vault import Vault, VaultError


class ChecksumError(Exception):
    """Raised when checksum operations fail."""


def compute_checksum(vault: Vault, password: str, algorithm: str = "sha256") -> str:
    """Compute a deterministic checksum over all key-value pairs in the vault.

    Keys are sorted to ensure consistent ordering regardless of insertion order.

    Args:
        vault: The Vault instance to checksum.
        password: Password used to decrypt vault secrets.
        algorithm: Hash algorithm name (default: sha256).

    Returns:
        Hex-digest string of the computed checksum.

    Raises:
        ChecksumError: If the algorithm is unsupported or vault cannot be read.
    """
    if algorithm not in hashlib.algorithms_guaranteed:
        raise ChecksumError(f"Unsupported hash algorithm: {algorithm!r}")

    try:
        keys = vault.list()
    except VaultError as exc:
        raise ChecksumError(f"Failed to list vault keys: {exc}") from exc

    pairs: Dict[str, str] = {}
    for key in sorted(keys):
        value = vault.get(key, password)
        if value is not None:
            pairs[key] = value

    payload = json.dumps(pairs, sort_keys=True, separators=(",", ":"))
    h = hashlib.new(algorithm, payload.encode("utf-8"))
    return h.hexdigest()


def verify_checksum(
    vault: Vault,
    password: str,
    expected: str,
    algorithm: str = "sha256",
) -> bool:
    """Verify that the vault's current checksum matches an expected value.

    Args:
        vault: The Vault instance to verify.
        password: Password used to decrypt vault secrets.
        expected: Previously recorded checksum hex-digest.
        algorithm: Hash algorithm used when the expected checksum was created.

    Returns:
        True if the checksum matches, False otherwise.
    """
    current = compute_checksum(vault, password, algorithm=algorithm)
    return current == expected
