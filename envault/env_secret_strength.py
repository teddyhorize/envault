"""Secret strength checker for envault."""

import re
from dataclasses import dataclass, field
from typing import List

from envault.vault import Vault, VaultError


class StrengthError(Exception):
    """Raised when strength checking fails."""


@dataclass
class StrengthResult:
    key: str
    score: int          # 0-4
    label: str
    suggestions: List[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return f"<StrengthResult key={self.key!r} score={self.score} label={self.label!r}>"


_LABELS = ["very weak", "weak", "fair", "strong", "very strong"]


def _score_value(value: str) -> tuple:
    """Return (score 0-4, suggestions list) for a plaintext secret value."""
    suggestions = []
    score = 0

    if len(value) >= 8:
        score += 1
    else:
        suggestions.append("Use at least 8 characters.")

    if len(value) >= 16:
        score += 1
    else:
        suggestions.append("Use at least 16 characters for better security.")

    if re.search(r"[A-Z]", value) and re.search(r"[a-z]", value):
        score += 1
    else:
        suggestions.append("Mix uppercase and lowercase letters.")

    if re.search(r"\d", value):
        score += 1
    else:
        suggestions.append("Include at least one digit.")

    if re.search(r"[^A-Za-z0-9]", value):
        score += 1
    else:
        suggestions.append("Include at least one special character.")

    return min(score, 4), suggestions


def check_strength(vault: Vault, password: str, key: str) -> StrengthResult:
    """Check the strength of a single secret."""
    if not key:
        raise StrengthError("Key must not be empty.")
    value = vault.get(key, password)
    if value is None:
        raise StrengthError(f"Key not found: {key!r}")
    score, suggestions = _score_value(value)
    return StrengthResult(key=key, score=score, label=_LABELS[score], suggestions=suggestions)


def check_all_strengths(vault: Vault, password: str) -> List[StrengthResult]:
    """Check strength of every secret in the vault."""
    try:
        keys = vault.list_keys()
    except VaultError as exc:
        raise StrengthError(str(exc)) from exc
    return [check_strength(vault, password, k) for k in sorted(keys)]
