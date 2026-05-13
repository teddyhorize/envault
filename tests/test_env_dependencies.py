"""Tests for envault.env_dependencies."""
import pytest

from envault.vault import Vault
from envault.env_dependencies import (
    DependencyError,
    add_dependency,
    remove_dependency,
    get_dependencies,
    get_dependents,
    list_all_dependencies,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="secret")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("DB_URL", "postgres://localhost:5432/db")
    v.set("API_KEY", "abc123")
    return v


def test_add_dependency_and_get(vault):
    add_dependency(vault, "DB_URL", "DB_HOST")
    assert "DB_HOST" in get_dependencies(vault, "DB_URL")


def test_add_multiple_dependencies(vault):
    add_dependency(vault, "DB_URL", "DB_HOST")
    add_dependency(vault, "DB_URL", "DB_PORT")
    deps = get_dependencies(vault, "DB_URL")
    assert "DB_HOST" in deps
    assert "DB_PORT" in deps


def test_add_duplicate_dependency_is_idempotent(vault):
    add_dependency(vault, "DB_URL", "DB_HOST")
    add_dependency(vault, "DB_URL", "DB_HOST")
    assert get_dependencies(vault, "DB_URL").count("DB_HOST") == 1


def test_add_dependency_missing_key_raises(vault):
    with pytest.raises(DependencyError, match="not found"):
        add_dependency(vault, "MISSING", "DB_HOST")


def test_add_dependency_missing_depends_on_raises(vault):
    with pytest.raises(DependencyError, match="not found"):
        add_dependency(vault, "DB_URL", "MISSING")


def test_add_dependency_empty_key_raises(vault):
    with pytest.raises(DependencyError, match="empty"):
        add_dependency(vault, "", "DB_HOST")


def test_add_dependency_self_raises(vault):
    with pytest.raises(DependencyError, match="itself"):
        add_dependency(vault, "DB_HOST", "DB_HOST")


def test_remove_dependency(vault):
    add_dependency(vault, "DB_URL", "DB_HOST")
    remove_dependency(vault, "DB_URL", "DB_HOST")
    assert get_dependencies(vault, "DB_URL") == []


def test_remove_nonexistent_dependency_raises(vault):
    with pytest.raises(DependencyError, match="no dependency"):
        remove_dependency(vault, "DB_URL", "DB_HOST")


def test_get_dependencies_empty_when_none_set(vault):
    assert get_dependencies(vault, "API_KEY") == []


def test_get_dependents_reverse_lookup(vault):
    add_dependency(vault, "DB_URL", "DB_HOST")
    add_dependency(vault, "DB_URL", "DB_PORT")
    dependents = get_dependents(vault, "DB_HOST")
    assert "DB_URL" in dependents


def test_get_dependents_empty_when_none(vault):
    assert get_dependents(vault, "API_KEY") == []


def test_list_all_dependencies(vault):
    add_dependency(vault, "DB_URL", "DB_HOST")
    add_dependency(vault, "DB_URL", "DB_PORT")
    all_deps = list_all_dependencies(vault)
    assert "DB_URL" in all_deps
    assert set(all_deps["DB_URL"]) == {"DB_HOST", "DB_PORT"}


def test_list_all_dependencies_empty_vault(vault):
    assert list_all_dependencies(vault) == {}
