"""Tests for envault.vault module."""

import pytest

from envault.vault import Vault, VaultError


PASSWORD = "test-password-123"


@pytest.fixture()
def vault(tmp_path):
    return Vault(path=str(tmp_path / ".envault"), password=PASSWORD)


def test_set_and_get_secret(vault):
    vault.set("DB_HOST", "localhost")
    assert vault.get("DB_HOST") == "localhost"


def test_get_missing_key_returns_none(vault):
    assert vault.get("NONEXISTENT") is None


def test_set_empty_key_raises(vault):
    with pytest.raises(VaultError):
        vault.set("", "value")


def test_delete_existing_key(vault):
    vault.set("TOKEN", "abc123")
    removed = vault.delete("TOKEN")
    assert removed is True
    assert vault.get("TOKEN") is None


def test_delete_missing_key_returns_false(vault):
    assert vault.delete("GHOST_KEY") is False


def test_list_keys_sorted(vault):
    vault.set("ZEBRA", "1")
    vault.set("APPLE", "2")
    vault.set("MANGO", "3")
    assert vault.list_keys() == ["APPLE", "MANGO", "ZEBRA"]


def test_persistence_across_instances(tmp_path):
    path = str(tmp_path / ".envault")
    v1 = Vault(path=path, password=PASSWORD)
    v1.set("SECRET", "hunter2")

    v2 = Vault(path=path, password=PASSWORD)
    assert v2.get("SECRET") == "hunter2"


def test_wrong_password_raises_on_load(tmp_path):
    path = str(tmp_path / ".envault")
    v1 = Vault(path=path, password=PASSWORD)
    v1.set("KEY", "value")

    with pytest.raises(VaultError):
        Vault(path=path, password="wrong-password")


def test_export_env_format(vault):
    vault.set("PORT", "8080")
    vault.set("HOST", "0.0.0.0")
    output = vault.export_env()
    assert "HOST=0.0.0.0" in output
    assert "PORT=8080" in output


def test_overwrite_existing_key(vault):
    vault.set("API_KEY", "old")
    vault.set("API_KEY", "new")
    assert vault.get("API_KEY") == "new"
    assert vault.list_keys() == ["API_KEY"]
