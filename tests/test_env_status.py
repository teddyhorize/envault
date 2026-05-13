"""Tests for envault.env_status module."""

import time
import pytest

from envault.vault import Vault
from envault.expiry import set_expiry
from envault.env_pin import pin_secret
from envault.env_status import get_vault_status, VaultStatus, KeyStatus, StatusError


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="pass")
    v.set("API_KEY", "abc123")
    v.set("DB_PASS", "secret")
    v.set("TOKEN", "tok")
    return v


def test_status_returns_vault_status(vault):
    status = get_vault_status(vault)
    assert isinstance(status, VaultStatus)


def test_status_total_keys(vault):
    status = get_vault_status(vault)
    assert status.total_keys == 3


def test_status_no_expired_initially(vault):
    status = get_vault_status(vault)
    assert status.expired_keys == []


def test_status_detects_expired_key(vault):
    set_expiry(vault, "API_KEY", seconds=-1)  # already expired
    status = get_vault_status(vault)
    assert "API_KEY" in status.expired_keys


def test_status_detects_pinned_key(vault):
    pin_secret(vault, "DB_PASS")
    status = get_vault_status(vault)
    assert "DB_PASS" in status.pinned_keys


def test_status_key_statuses_length(vault):
    status = get_vault_status(vault)
    assert len(status.key_statuses) == 3


def test_status_key_status_pinned_flag(vault):
    pin_secret(vault, "TOKEN")
    status = get_vault_status(vault)
    token_status = next(ks for ks in status.key_statuses if ks.key == "TOKEN")
    assert token_status.pinned is True


def test_status_key_status_not_pinned_flag(vault):
    status = get_vault_status(vault)
    api_status = next(ks for ks in status.key_statuses if ks.key == "API_KEY")
    assert api_status.pinned is False


def test_status_summary_contains_vault_path(vault):
    status = get_vault_status(vault)
    summary = status.summary()
    assert vault.path in summary


def test_status_summary_contains_key_count(vault):
    status = get_vault_status(vault)
    summary = status.summary()
    assert "3" in summary


def test_key_status_repr_expired(vault):
    set_expiry(vault, "API_KEY", seconds=-1)
    status = get_vault_status(vault)
    api_status = next(ks for ks in status.key_statuses if ks.key == "API_KEY")
    assert "EXPIRED" in repr(api_status)


def test_status_empty_vault(tmp_path):
    v = Vault(str(tmp_path / "empty.vault"), password="pass")
    status = get_vault_status(v)
    assert status.total_keys == 0
    assert status.expired_keys == []
    assert status.pinned_keys == []
