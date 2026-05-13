"""Tests for envault.env_group module."""

import pytest
from pathlib import Path

from envault.vault import Vault
from envault.env_group import (
    GroupError,
    define_group,
    delete_group,
    list_groups,
    get_group,
    resolve_group,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="secret")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "abc123")
    v.set("API_SECRET", "xyz789")
    return v


def test_define_group_and_list(vault):
    define_group(vault, "database", ["DB_HOST", "DB_PORT"])
    groups = list_groups(vault)
    assert "database" in groups
    assert groups["database"] == ["DB_HOST", "DB_PORT"]


def test_define_multiple_groups(vault):
    define_group(vault, "database", ["DB_HOST", "DB_PORT"])
    define_group(vault, "api", ["API_KEY", "API_SECRET"])
    groups = list_groups(vault)
    assert "database" in groups
    assert "api" in groups


def test_define_group_empty_name_raises(vault):
    with pytest.raises(GroupError, match="empty"):
        define_group(vault, "", ["DB_HOST"])


def test_define_group_empty_keys_raises(vault):
    with pytest.raises(GroupError, match="at least one key"):
        define_group(vault, "empty", [])


def test_define_group_missing_key_raises(vault):
    with pytest.raises(GroupError, match="MISSING_KEY"):
        define_group(vault, "bad", ["DB_HOST", "MISSING_KEY"])


def test_get_group_returns_keys(vault):
    define_group(vault, "database", ["DB_HOST", "DB_PORT"])
    keys = get_group(vault, "database")
    assert keys == ["DB_HOST", "DB_PORT"]


def test_get_group_nonexistent_returns_none(vault):
    assert get_group(vault, "nonexistent") is None


def test_delete_group(vault):
    define_group(vault, "database", ["DB_HOST", "DB_PORT"])
    delete_group(vault, "database")
    assert get_group(vault, "database") is None


def test_delete_nonexistent_group_raises(vault):
    with pytest.raises(GroupError, match="does not exist"):
        delete_group(vault, "ghost")


def test_resolve_group_returns_values(vault):
    define_group(vault, "database", ["DB_HOST", "DB_PORT"])
    result = resolve_group(vault, "database")
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_resolve_nonexistent_group_raises(vault):
    with pytest.raises(GroupError, match="does not exist"):
        resolve_group(vault, "ghost")


def test_define_group_overwrites_existing(vault):
    define_group(vault, "database", ["DB_HOST", "DB_PORT"])
    define_group(vault, "database", ["DB_HOST"])
    assert get_group(vault, "database") == ["DB_HOST"]
