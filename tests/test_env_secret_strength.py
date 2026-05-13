"""Tests for envault.env_secret_strength."""

import pytest

from envault.vault import Vault
from envault.env_secret_strength import (
    StrengthError,
    StrengthResult,
    check_strength,
    check_all_strengths,
)


PASSWORD = "test-password"


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.db"), PASSWORD)
    v.set("WEAK", "abc", PASSWORD)
    v.set("MEDIUM", "Hello123", PASSWORD)
    v.set("STRONG", "G7#kLp!2xQrT9mNv", PASSWORD)
    return v


def test_check_strength_returns_result(vault):
    result = check_strength(vault, PASSWORD, "WEAK")
    assert isinstance(result, StrengthResult)
    assert result.key == "WEAK"


def test_weak_secret_low_score(vault):
    result = check_strength(vault, PASSWORD, "WEAK")
    assert result.score <= 1
    assert result.label in ("very weak", "weak")


def test_weak_secret_has_suggestions(vault):
    result = check_strength(vault, PASSWORD, "WEAK")
    assert len(result.suggestions) > 0


def test_medium_secret_mid_score(vault):
    result = check_strength(vault, PASSWORD, "MEDIUM")
    assert 1 <= result.score <= 3


def test_strong_secret_high_score(vault):
    result = check_strength(vault, PASSWORD, "STRONG")
    assert result.score >= 3
    assert result.label in ("strong", "very strong")


def test_strong_secret_fewer_suggestions(vault):
    result = check_strength(vault, PASSWORD, "STRONG")
    assert len(result.suggestions) <= 1


def test_missing_key_raises(vault):
    with pytest.raises(StrengthError, match="Key not found"):
        check_strength(vault, PASSWORD, "NONEXISTENT")


def test_empty_key_raises(vault):
    with pytest.raises(StrengthError, match="empty"):
        check_strength(vault, PASSWORD, "")


def test_check_all_returns_list(vault):
    results = check_all_strengths(vault, PASSWORD)
    assert isinstance(results, list)
    assert len(results) == 3


def test_check_all_keys_sorted(vault):
    results = check_all_strengths(vault, PASSWORD)
    keys = [r.key for r in results]
    assert keys == sorted(keys)


def test_repr_contains_key_and_label(vault):
    result = check_strength(vault, PASSWORD, "WEAK")
    r = repr(result)
    assert "WEAK" in r
    assert result.label in r
