"""Tests for envault.env_readonly."""

import pytest
from pathlib import Path
from envault.vault import Vault
from envault.env_readonly import (
    ReadOnlyError,
    protect,
    unprotect,
    is_protected,
    list_protected,
    assert_writable,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), "password")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "secret")
    return v


def test_protect_marks_key_as_readonly(vault):
    protect(vault, "DB_HOST")
    assert is_protected(vault, "DB_HOST")


def test_unprotect_removes_protection(vault):
    protect(vault, "DB_HOST")
    unprotect(vault, "DB_HOST")
    assert not is_protected(vault, "DB_HOST")


def test_is_protected_false_when_not_set(vault):
    assert not is_protected(vault, "DB_HOST")


def test_protect_missing_key_raises(vault):
    with pytest.raises(ReadOnlyError, match="does not exist"):
        protect(vault, "MISSING_KEY")


def test_protect_empty_key_raises(vault):
    with pytest.raises(ReadOnlyError, match="empty"):
        protect(vault, "")


def test_unprotect_empty_key_raises(vault):
    with pytest.raises(ReadOnlyError, match="empty"):
        unprotect(vault, "")


def test_list_protected_returns_sorted(vault):
    protect(vault, "DB_PORT")
    protect(vault, "API_KEY")
    protect(vault, "DB_HOST")
    result = list_protected(vault)
    assert result == ["API_KEY", "DB_HOST", "DB_PORT"]


def test_list_protected_empty_when_none(vault):
    assert list_protected(vault) == []


def test_assert_writable_raises_for_protected(vault):
    protect(vault, "API_KEY")
    with pytest.raises(ReadOnlyError, match="read-only"):
        assert_writable(vault, "API_KEY")


def test_assert_writable_passes_for_unprotected(vault):
    assert_writable(vault, "DB_HOST")  # should not raise


def test_unprotect_nonexistent_key_is_safe(vault):
    unprotect(vault, "NONEXISTENT")  # should not raise


def test_protect_multiple_keys(vault):
    protect(vault, "DB_HOST")
    protect(vault, "API_KEY")
    assert is_protected(vault, "DB_HOST")
    assert is_protected(vault, "API_KEY")
    assert not is_protected(vault, "DB_PORT")


def test_protect_duplicate_is_idempotent(vault):
    protect(vault, "DB_HOST")
    protect(vault, "DB_HOST")
    assert list_protected(vault).count("DB_HOST") == 1
