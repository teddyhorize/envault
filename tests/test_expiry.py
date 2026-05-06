"""Tests for envault.expiry module."""

from __future__ import annotations

import time
import pytest

from envault.vault import Vault
from envault.expiry import (
    ExpiryError,
    set_expiry,
    get_expiry,
    is_expired,
    purge_expired,
)

_PASSWORD = "test-password-expiry"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), _PASSWORD)
    v.set("API_KEY", "abc123")
    v.set("DB_PASS", "secret")
    v.set("TOKEN", "tok_xyz")
    return v


def test_set_expiry_returns_future_timestamp(vault):
    ts = set_expiry(vault, "API_KEY", ttl_seconds=60)
    assert ts > time.time()


def test_get_expiry_returns_none_when_not_set(vault):
    assert get_expiry(vault, "API_KEY") is None


def test_get_expiry_returns_timestamp_after_set(vault):
    set_expiry(vault, "API_KEY", ttl_seconds=120)
    ts = get_expiry(vault, "API_KEY")
    assert ts is not None
    assert ts > time.time()


def test_is_expired_false_for_future_expiry(vault):
    set_expiry(vault, "API_KEY", ttl_seconds=3600)
    assert is_expired(vault, "API_KEY") is False


def test_is_expired_false_when_no_expiry_set(vault):
    assert is_expired(vault, "DB_PASS") is False


def test_is_expired_true_for_past_expiry(vault):
    set_expiry(vault, "TOKEN", ttl_seconds=0.001)
    time.sleep(0.05)
    assert is_expired(vault, "TOKEN") is True


def test_purge_expired_removes_expired_keys(vault):
    set_expiry(vault, "TOKEN", ttl_seconds=0.001)
    time.sleep(0.05)
    purged = purge_expired(vault, _PASSWORD)
    assert "TOKEN" in purged
    assert vault.get("TOKEN") is None


def test_purge_expired_leaves_valid_keys(vault):
    set_expiry(vault, "API_KEY", ttl_seconds=3600)
    set_expiry(vault, "TOKEN", ttl_seconds=0.001)
    time.sleep(0.05)
    purged = purge_expired(vault, _PASSWORD)
    assert "TOKEN" in purged
    assert "API_KEY" not in purged
    assert vault.get("API_KEY") == "abc123"


def test_set_expiry_missing_key_raises(vault):
    with pytest.raises(ExpiryError, match="does not exist"):
        set_expiry(vault, "NONEXISTENT", ttl_seconds=60)


def test_set_expiry_empty_key_raises(vault):
    with pytest.raises(ExpiryError, match="empty"):
        set_expiry(vault, "", ttl_seconds=60)


def test_set_expiry_non_positive_ttl_raises(vault):
    with pytest.raises(ExpiryError, match="positive"):
        set_expiry(vault, "API_KEY", ttl_seconds=-10)
