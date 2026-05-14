"""Secret value formatting utilities for envault."""

from __future__ import annotations

import re
from typing import Optional


class FormatError(Exception):
    """Raised when a formatting operation fails."""


_FORMATS = {
    "upper": str.upper,
    "lower": str.lower,
    "strip": str.strip,
    "base64": lambda v: __import__("base64").b64encode(v.encode()).decode(),
    "unbase64": lambda v: __import__("base64").b64decode(v.encode()).decode(),
}

VALID_FORMATS = list(_FORMATS.keys())


def apply_format(value: str, fmt: str) -> str:
    """Apply a named format transformation to a secret value."""
    if not fmt:
        raise FormatError("Format name must not be empty.")
    if fmt not in _FORMATS:
        raise FormatError(
            f"Unknown format '{fmt}'. Valid formats: {', '.join(VALID_FORMATS)}"
        )
    try:
        return _FORMATS[fmt](value)
    except Exception as exc:
        raise FormatError(f"Failed to apply format '{fmt}': {exc}") from exc


def format_secret(vault, key: str, fmt: str) -> str:
    """Read a secret from *vault*, apply *fmt*, and return the formatted value.

    Does **not** modify the vault — callers decide whether to store the result.
    """
    if not key:
        raise FormatError("Key must not be empty.")
    value = vault.get(key)
    if value is None:
        raise FormatError(f"Key '{key}' not found in vault.")
    return apply_format(value, fmt)


def format_and_store(vault, key: str, fmt: str, dest_key: Optional[str] = None) -> str:
    """Apply *fmt* to the value at *key* and store the result.

    If *dest_key* is given the formatted value is written to that key;
    otherwise the original *key* is overwritten.

    Returns the formatted value.
    """
    formatted = format_secret(vault, key, fmt)
    target = dest_key if dest_key else key
    if not target:
        raise FormatError("Destination key must not be empty.")
    vault.set(target, formatted)
    return formatted
