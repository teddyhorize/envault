"""Vault linting: detect common issues with secret keys and values."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from envault.vault import Vault


class LintError(Exception):
    """Raised when linting cannot be performed."""


@dataclass
class LintIssue:
    key: str
    severity: str  # 'warning' or 'error'
    message: str

    def __repr__(self) -> str:
        return f"[{self.severity.upper()}] {self.key}: {self.message}"


@dataclass
class LintResult:
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return len(self.issues) > 0

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]

    def summary(self) -> str:
        if not self.has_issues:
            return "No issues found."
        return (
            f"{len(self.errors)} error(s), {len(self.warnings)} warning(s) found."
        )


_KEY_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")
_PLACEHOLDER_PATTERN = re.compile(r"^(CHANGE_ME|TODO|FIXME|PLACEHOLDER|<.*>)$", re.IGNORECASE)


def lint_vault(vault: Vault, password: str) -> LintResult:
    """Run all lint checks against a vault and return a LintResult."""
    if not isinstance(vault, Vault):
        raise LintError("Expected a Vault instance.")

    result = LintResult()
    keys = vault.list_keys()

    if not keys:
        result.issues.append(
            LintIssue(key="<vault>", severity="warning", message="Vault is empty.")
        )
        return result

    for key in keys:
        # Key naming convention
        if not _KEY_PATTERN.match(key):
            result.issues.append(
                LintIssue(
                    key=key,
                    severity="warning",
                    message="Key should be UPPER_SNAKE_CASE (A-Z, 0-9, underscore, must start with a letter).",
                )
            )

        value = vault.get(key, password)
        if value is None:
            continue

        # Empty value
        if value.strip() == "":
            result.issues.append(
                LintIssue(key=key, severity="error", message="Value is empty or whitespace.")
            )
            continue

        # Placeholder value
        if _PLACEHOLDER_PATTERN.match(value.strip()):
            result.issues.append(
                LintIssue(key=key, severity="error", message=f"Value looks like a placeholder: '{value}'.")
            )

        # Very short value (potential weak secret)
        if len(value) < 8:
            result.issues.append(
                LintIssue(key=key, severity="warning", message="Value is very short (< 8 chars); may be a weak secret.")
            )

    return result
