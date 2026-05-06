"""Search and filter secrets in a vault by key pattern or tag."""

from __future__ import annotations

import fnmatch
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError
from envault.tags import get_tags


class SearchError(Exception):
    """Raised when a search operation fails."""


def search_by_pattern(
    vault: Vault,
    pattern: str,
    password: str,
) -> Dict[str, str]:
    """Return secrets whose keys match a glob-style pattern.

    Args:
        vault: An open Vault instance.
        pattern: A glob pattern (e.g. ``DB_*``, ``*SECRET*``).
        password: Vault password used to decrypt values.

    Returns:
        Mapping of matching key -> plaintext value.

    Raises:
        SearchError: If the pattern is empty.
    """
    if not pattern:
        raise SearchError("Search pattern must not be empty.")

    keys = vault.keys()
    matched: Dict[str, str] = {}
    for key in keys:
        if fnmatch.fnmatch(key, pattern):
            value = vault.get(key, password)
            if value is not None:
                matched[key] = value
    return matched


def search_by_tag(
    vault: Vault,
    tag: str,
    password: str,
) -> Dict[str, str]:
    """Return secrets that carry a specific tag.

    Args:
        vault: An open Vault instance.
        tag: The tag to filter by.
        password: Vault password used to decrypt values.

    Returns:
        Mapping of matching key -> plaintext value.

    Raises:
        SearchError: If the tag string is empty.
    """
    if not tag:
        raise SearchError("Tag must not be empty.")

    keys = vault.keys()
    matched: Dict[str, str] = {}
    for key in keys:
        tags = get_tags(vault, key)
        if tag in tags:
            value = vault.get(key, password)
            if value is not None:
                matched[key] = value
    return matched
