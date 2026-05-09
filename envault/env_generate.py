"""Secret generation utilities for envault."""

import secrets
import string

from envault.vault import Vault, VaultError


class GenerateError(Exception):
    """Raised when secret generation fails."""


DEFAULT_LENGTH = 32
DEFAULT_ALPHABET = string.ascii_letters + string.digits + string.punctuation
ALPHABET_ALPHANUMERIC = string.ascii_letters + string.digits
ALPHABET_HEX = string.hexdigits[:16]  # lowercase hex
ALPHABET_NUMERIC = string.digits

_PRESETS = {
    "default": DEFAULT_ALPHABET,
    "alphanumeric": ALPHABET_ALPHANUMERIC,
    "hex": ALPHABET_HEX,
    "numeric": ALPHABET_NUMERIC,
}


def generate_secret(length: int = DEFAULT_LENGTH, charset: str = "default") -> str:
    """Generate a cryptographically secure random secret string.

    Args:
        length: Number of characters to generate. Must be >= 1.
        charset: Named preset ('default', 'alphanumeric', 'hex', 'numeric')
                 or a custom alphabet string.

    Returns:
        A random secret string of the requested length.

    Raises:
        GenerateError: If length < 1 or charset is empty.
    """
    if length < 1:
        raise GenerateError(f"Length must be at least 1, got {length}")

    alphabet = _PRESETS.get(charset, charset)
    if not alphabet:
        raise GenerateError("Charset/alphabet must not be empty")

    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_and_store(
    vault: Vault,
    key: str,
    length: int = DEFAULT_LENGTH,
    charset: str = "default",
    overwrite: bool = False,
) -> str:
    """Generate a secret and store it in the vault.

    Args:
        vault: Target Vault instance.
        key: Secret key name.
        length: Length of the generated secret.
        charset: Character set preset or custom alphabet.
        overwrite: If False and key already exists, raises GenerateError.

    Returns:
        The generated secret value.

    Raises:
        GenerateError: If key exists and overwrite is False, or on bad params.
        VaultError: Propagated from vault operations.
    """
    if not key:
        raise GenerateError("Key must not be empty")

    if not overwrite and vault.get(key) is not None:
        raise GenerateError(
            f"Key '{key}' already exists. Use overwrite=True to replace it."
        )

    value = generate_secret(length=length, charset=charset)
    vault.set(key, value)
    return value
