"""Tests for envault.env_alias."""

from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.env_alias import (
    AliasError,
    add_alias,
    remove_alias,
    resolve_alias,
    list_aliases,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="secret")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    return v


def test_add_alias_and_resolve(vault):
    add_alias(vault, "database_host", "DB_HOST")
    assert resolve_alias(vault, "database_host") == "localhost"


def test_resolve_nonexistent_alias_returns_none(vault):
    assert resolve_alias(vault, "ghost") is None


def test_add_alias_missing_target_raises(vault):
    with pytest.raises(AliasError, match="does not exist"):
        add_alias(vault, "my_alias", "MISSING_KEY")


def test_add_alias_empty_name_raises(vault):
    with pytest.raises(AliasError, match="empty"):
        add_alias(vault, "", "DB_HOST")


def test_add_alias_empty_target_raises(vault):
    with pytest.raises(AliasError, match="empty"):
        add_alias(vault, "my_alias", "")


def test_remove_alias(vault):
    add_alias(vault, "host_alias", "DB_HOST")
    remove_alias(vault, "host_alias")
    assert resolve_alias(vault, "host_alias") is None


def test_remove_nonexistent_alias_raises(vault):
    with pytest.raises(AliasError, match="does not exist"):
        remove_alias(vault, "no_such_alias")


def test_list_aliases_empty(vault):
    assert list_aliases(vault) == {}


def test_list_aliases_multiple(vault):
    add_alias(vault, "host", "DB_HOST")
    add_alias(vault, "port", "DB_PORT")
    result = list_aliases(vault)
    assert result == {"host": "DB_HOST", "port": "DB_PORT"}


def test_alias_reflects_updated_target(vault):
    add_alias(vault, "host", "DB_HOST")
    vault.set("DB_HOST", "remotehost")
    assert resolve_alias(vault, "host") == "remotehost"


def test_add_alias_overwrites_existing(vault):
    add_alias(vault, "db", "DB_HOST")
    add_alias(vault, "db", "DB_PORT")
    assert list_aliases(vault)["db"] == "DB_PORT"
