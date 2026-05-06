"""Import/export secrets to/from plain .env file format."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class EnvFileError(Exception):
    """Raised when an .env file cannot be parsed or written."""


_LINE_RE = re.compile(r'^(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$')


def parse_env_file(path: str) -> Dict[str, str]:
    """Parse a .env file and return a dict of key/value pairs.

    Supports optional 'export' prefix and strips surrounding quotes.
    Lines starting with '#' and blank lines are ignored.
    """
    result: Dict[str, str] = {}
    text = Path(path).read_text(encoding="utf-8")
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = _LINE_RE.match(line)
        if not m:
            raise EnvFileError(f"Unparseable line {lineno}: {raw!r}")
        key, value = m.group(1), m.group(2)
        # Strip matching surrounding quotes
        if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
            value = value[1:-1]
        result[key] = value
    return result


def import_from_env_file(
    vault: Vault,
    path: str,
    overwrite: bool = True,
) -> List[str]:
    """Import secrets from a .env file into *vault*.

    Returns the list of keys that were imported.
    Raises EnvFileError if the file cannot be parsed.
    """
    pairs = parse_env_file(path)
    if not pairs:
        raise EnvFileError(f"No secrets found in {path!r}")
    imported: List[str] = []
    for key, value in pairs.items():
        if not overwrite and vault.get(key) is not None:
            continue
        vault.set(key, value)
        imported.append(key)
    return imported


def export_to_env_file(
    vault: Vault,
    path: str,
    keys: Optional[List[str]] = None,
) -> List[str]:
    """Export secrets from *vault* to a plain .env file.

    If *keys* is given only those keys are exported.
    Returns the list of keys written.
    Raises EnvFileError if no secrets are available to export.
    """
    all_keys = keys if keys is not None else vault.list_keys()
    if not all_keys:
        raise EnvFileError("No secrets to export.")
    lines: List[str] = []
    exported: List[str] = []
    for key in all_keys:
        value = vault.get(key)
        if value is None:
            continue
        # Quote values that contain spaces or special chars
        if any(c in value for c in (' ', '"', "'", '\n', '\t')):
            escaped = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped}"')
        else:
            lines.append(f"{key}={value}")
        exported.append(key)
    if not exported:
        raise EnvFileError("No secrets to export.")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return exported
