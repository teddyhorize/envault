"""Template support for envault: define and apply secret templates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class TemplateError(Exception):
    """Raised when a template operation fails."""


def _template_path(vault: Vault) -> Path:
    return Path(vault.path).parent / (Path(vault.path).stem + ".templates.json")


def _load_templates(vault: Vault) -> Dict[str, List[str]]:
    path = _template_path(vault)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise TemplateError(f"Failed to load templates: {exc}") from exc


def _save_templates(vault: Vault, templates: Dict[str, List[str]]) -> None:
    path = _template_path(vault)
    try:
        path.write_text(json.dumps(templates, indent=2))
    except OSError as exc:
        raise TemplateError(f"Failed to save templates: {exc}") from exc


def define_template(vault: Vault, name: str, keys: List[str]) -> None:
    """Define a named template with a list of required secret keys."""
    if not name or not name.strip():
        raise TemplateError("Template name must not be empty.")
    if not keys:
        raise TemplateError("Template must contain at least one key.")
    templates = _load_templates(vault)
    templates[name] = list(keys)
    _save_templates(vault, templates)


def delete_template(vault: Vault, name: str) -> None:
    """Remove a named template."""
    templates = _load_templates(vault)
    if name not in templates:
        raise TemplateError(f"Template '{name}' not found.")
    del templates[name]
    _save_templates(vault, templates)


def list_templates(vault: Vault) -> Dict[str, List[str]]:
    """Return all defined templates."""
    return _load_templates(vault)


def validate_against_template(
    vault: Vault, name: str, password: str
) -> List[str]:
    """Return a list of keys required by the template that are missing from the vault."""
    templates = _load_templates(vault)
    if name not in templates:
        raise TemplateError(f"Template '{name}' not found.")
    missing: List[str] = []
    for key in templates[name]:
        try:
            value = vault.get(key, password)
            if value is None:
                missing.append(key)
        except VaultError:
            missing.append(key)
    return missing


def apply_template(
    vault: Vault, name: str, values: Dict[str, str], password: str
) -> int:
    """Set all keys defined in the template from the provided values dict.

    Returns the number of keys written.
    """
    templates = _load_templates(vault)
    if name not in templates:
        raise TemplateError(f"Template '{name}' not found.")
    written = 0
    for key in templates[name]:
        if key not in values:
            raise TemplateError(
                f"Key '{key}' required by template '{name}' not provided."
            )
        vault.set(key, values[key], password)
        written += 1
    return written
