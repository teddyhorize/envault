"""Validation rules for vault secrets — type checks, required keys, regex patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class ValidationError(Exception):
    """Raised when validation setup is invalid."""


@dataclass
class ValidationIssue:
    key: str
    rule: str
    message: str

    def __repr__(self) -> str:
        return f"[{self.rule}] {self.key}: {self.message}"


@dataclass
class ValidationResult:
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    def summary(self) -> str:
        if not self.has_issues:
            return "All validations passed."
        lines = [f"{len(self.issues)} validation issue(s) found:"]
        for issue in self.issues:
            lines.append(f"  {issue}")
        return "\n".join(lines)


def validate_vault(
    vault: Vault,
    password: str,
    required_keys: Optional[List[str]] = None,
    patterns: Optional[Dict[str, str]] = None,
    non_empty: bool = True,
) -> ValidationResult:
    """Validate vault secrets against a set of rules.

    Args:
        vault: The Vault instance to validate.
        password: Password to decrypt secrets.
        required_keys: Keys that must be present in the vault.
        patterns: Mapping of key -> regex pattern the value must match.
        non_empty: If True, flag any secret whose value is an empty string.

    Returns:
        A ValidationResult containing any discovered issues.
    """
    if patterns is None:
        patterns = {}
    if required_keys is None:
        required_keys = []

    result = ValidationResult()

    try:
        all_keys = vault.list_keys()
    except VaultError as exc:
        raise ValidationError(f"Could not list vault keys: {exc}") from exc

    # Required-key check
    for key in required_keys:
        if key not in all_keys:
            result.issues.append(
                ValidationIssue(key=key, rule="required", message="Key is missing from vault.")
            )

    # Per-key value checks
    for key in all_keys:
        try:
            value = vault.get(key, password)
        except VaultError as exc:
            result.issues.append(
                ValidationIssue(key=key, rule="decrypt", message=f"Could not decrypt: {exc}")
            )
            continue

        if value is None:
            continue

        if non_empty and value == "":
            result.issues.append(
                ValidationIssue(key=key, rule="non_empty", message="Value is an empty string.")
            )

        if key in patterns:
            pattern = patterns[key]
            try:
                if not re.fullmatch(pattern, value):
                    result.issues.append(
                        ValidationIssue(
                            key=key,
                            rule="pattern",
                            message=f"Value does not match pattern '{pattern}'.",
                        )
                    )
            except re.error as exc:
                raise ValidationError(f"Invalid regex for key '{key}': {exc}") from exc

    return result
