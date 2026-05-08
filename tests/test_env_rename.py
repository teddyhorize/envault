"""Tests for envault.env_rename."""

import pytest

from envault.vault import Vault
from envault.env_rename import RenameError, rename_secret, rename_prefix


@pytest.fixture()
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.env"), password="test-pass")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("APP_SECRET", "abc123")
    v.set("APP_DEBUG", "true")
    return v


def test_rename_secret_updates_key(vault):
    rename_secret(vault, "DB_HOST", "DATABASE_HOST")
    assert vault.get("DATABASE_HOST") == "localhost"


def test_rename_secret_removes_old_key(vault):
    rename_secret(vault, "DB_HOST", "DATABASE_HOST")
    assert vault.get("DB_HOST") is None


def test_rename_secret_missing_key_raises(vault):
    with pytest.raises(RenameError, match="Key not found"):
        rename_secret(vault, "NONEXISTENT", "NEW_KEY")


def test_rename_secret_empty_old_key_raises(vault):
    with pytest.raises(RenameError, match="old_key must not be empty"):
        rename_secret(vault, "", "NEW_KEY")


def test_rename_secret_empty_new_key_raises(vault):
    with pytest.raises(RenameError, match="new_key must not be empty"):
        rename_secret(vault, "DB_HOST", "")


def test_rename_secret_same_key_raises(vault):
    with pytest.raises(RenameError, match="must differ"):
        rename_secret(vault, "DB_HOST", "DB_HOST")


def test_rename_secret_existing_target_raises_without_overwrite(vault):
    with pytest.raises(RenameError, match="already exists"):
        rename_secret(vault, "DB_HOST", "DB_PORT")


def test_rename_secret_existing_target_allowed_with_overwrite(vault):
    rename_secret(vault, "DB_HOST", "DB_PORT", overwrite=True)
    assert vault.get("DB_PORT") == "localhost"
    assert vault.get("DB_HOST") is None


def test_rename_prefix_renames_all_matching_keys(vault):
    pairs = rename_prefix(vault, "DB_", "DATABASE_")
    assert len(pairs) == 2
    assert vault.get("DATABASE_HOST") == "localhost"
    assert vault.get("DATABASE_PORT") == "5432"


def test_rename_prefix_returns_old_new_pairs(vault):
    pairs = rename_prefix(vault, "APP_", "SERVICE_")
    old_keys = {p[0] for p in pairs}
    new_keys = {p[1] for p in pairs}
    assert old_keys == {"APP_SECRET", "APP_DEBUG"}
    assert new_keys == {"SERVICE_SECRET", "SERVICE_DEBUG"}


def test_rename_prefix_removes_old_keys(vault):
    rename_prefix(vault, "DB_", "DATABASE_")
    assert vault.get("DB_HOST") is None
    assert vault.get("DB_PORT") is None


def test_rename_prefix_no_match_raises(vault):
    with pytest.raises(RenameError, match="No keys found with prefix"):
        rename_prefix(vault, "MISSING_", "OTHER_")


def test_rename_prefix_empty_old_prefix_raises(vault):
    with pytest.raises(RenameError, match="old_prefix must not be empty"):
        rename_prefix(vault, "", "NEW_")


def test_rename_prefix_empty_new_prefix_raises(vault):
    with pytest.raises(RenameError, match="new_prefix must not be empty"):
        rename_prefix(vault, "DB_", "")
