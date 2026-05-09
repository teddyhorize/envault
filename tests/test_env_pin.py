"""Tests for envault/env_pin.py"""

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_pin import (
    PinError,
    pin_secret,
    unpin_secret,
    is_pinned,
    list_pinned,
    assert_not_pinned,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="testpass")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "secret-key")
    return v


def test_pin_secret_marks_key_as_pinned(vault):
    pin_secret(vault, "DB_HOST")
    assert is_pinned(vault, "DB_HOST") is True


def test_unpin_secret_removes_pin(vault):
    pin_secret(vault, "DB_HOST")
    unpin_secret(vault, "DB_HOST")
    assert is_pinned(vault, "DB_HOST") is False


def test_is_pinned_false_when_not_pinned(vault):
    assert is_pinned(vault, "DB_HOST") is False


def test_pin_duplicate_is_idempotent(vault):
    pin_secret(vault, "DB_HOST")
    pin_secret(vault, "DB_HOST")
    assert list_pinned(vault).count("DB_HOST") == 1


def test_list_pinned_returns_all_pinned_keys(vault):
    pin_secret(vault, "DB_HOST")
    pin_secret(vault, "API_KEY")
    pinned = list_pinned(vault)
    assert "DB_HOST" in pinned
    assert "API_KEY" in pinned
    assert len(pinned) == 2


def test_list_pinned_empty_when_none_pinned(vault):
    assert list_pinned(vault) == []


def test_pin_empty_key_raises(vault):
    with pytest.raises(PinError, match="empty"):
        pin_secret(vault, "")


def test_pin_missing_key_raises(vault):
    with pytest.raises(PinError, match="does not exist"):
        pin_secret(vault, "NONEXISTENT")


def test_unpin_empty_key_raises(vault):
    with pytest.raises(PinError, match="empty"):
        unpin_secret(vault, "")


def test_unpin_not_pinned_key_is_safe(vault):
    # Should not raise even if key was never pinned
    unpin_secret(vault, "DB_HOST")
    assert is_pinned(vault, "DB_HOST") is False


def test_assert_not_pinned_raises_when_pinned(vault):
    pin_secret(vault, "API_KEY")
    with pytest.raises(PinError, match="pinned"):
        assert_not_pinned(vault, "API_KEY", "modify")


def test_assert_not_pinned_passes_when_not_pinned(vault):
    # Should not raise
    assert_not_pinned(vault, "DB_HOST", "delete")
