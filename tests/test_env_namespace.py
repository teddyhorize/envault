"""Tests for envault.env_namespace."""
from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.env_namespace import (
    NamespaceError,
    define_namespace,
    list_namespaces,
    delete_namespace,
    get_secrets_in_namespace,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="pass")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("APP_SECRET", "abc123")
    v.set("APP_DEBUG", "true")
    v.set("UNRELATED", "value")
    return v


def test_define_namespace_and_list(vault):
    define_namespace(vault, "DB", "Database secrets")
    ns = list_namespaces(vault)
    assert "DB" in ns
    assert ns["DB"] == "Database secrets"


def test_define_multiple_namespaces(vault):
    define_namespace(vault, "DB")
    define_namespace(vault, "APP", "Application config")
    ns = list_namespaces(vault)
    assert "DB" in ns
    assert "APP" in ns


def test_define_namespace_empty_name_raises(vault):
    with pytest.raises(NamespaceError, match="must not be empty"):
        define_namespace(vault, "")


def test_define_namespace_overwrites_description(vault):
    define_namespace(vault, "DB", "old")
    define_namespace(vault, "DB", "new")
    ns = list_namespaces(vault)
    assert ns["DB"] == "new"


def test_list_namespaces_empty_when_none_defined(vault):
    ns = list_namespaces(vault)
    assert ns == {}


def test_delete_namespace_removes_it(vault):
    define_namespace(vault, "DB", "desc")
    delete_namespace(vault, "DB")
    ns = list_namespaces(vault)
    assert "DB" not in ns


def test_delete_nonexistent_namespace_raises(vault):
    with pytest.raises(NamespaceError, match="does not exist"):
        delete_namespace(vault, "MISSING")


def test_delete_empty_namespace_name_raises(vault):
    with pytest.raises(NamespaceError, match="must not be empty"):
        delete_namespace(vault, "")


def test_get_secrets_in_namespace_underscore_prefix(vault):
    secrets = get_secrets_in_namespace(vault, "DB")
    assert "DB_HOST" in secrets
    assert "DB_PORT" in secrets
    assert "APP_SECRET" not in secrets
    assert secrets["DB_HOST"] == "localhost"


def test_get_secrets_in_namespace_slash_prefix(vault):
    vault.set("APP/TOKEN", "tok")
    vault.set("APP/KEY", "key")
    secrets = get_secrets_in_namespace(vault, "APP")
    assert "APP/TOKEN" in secrets
    assert "APP/KEY" in secrets


def test_get_secrets_in_namespace_empty_name_raises(vault):
    with pytest.raises(NamespaceError, match="must not be empty"):
        get_secrets_in_namespace(vault, "")


def test_get_secrets_in_namespace_no_matches(vault):
    secrets = get_secrets_in_namespace(vault, "NONEXISTENT")
    assert secrets == {}
