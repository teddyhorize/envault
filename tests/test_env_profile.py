"""Tests for envault/env_profile.py"""

import pytest
from pathlib import Path
from envault.vault import Vault
from envault.env_profile import (
    ProfileError,
    define_profile,
    delete_profile,
    list_profiles,
    get_profile_keys,
    apply_profile,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="secret")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "abc123")
    v.set("REDIS_URL", "redis://localhost")
    return v


def test_define_profile_and_list(vault):
    define_profile(vault.path, "dev", ["DB_HOST", "DB_PORT"])
    assert "dev" in list_profiles(vault.path)


def test_define_multiple_profiles(vault):
    define_profile(vault.path, "dev", ["DB_HOST"])
    define_profile(vault.path, "prod", ["DB_HOST", "API_KEY"])
    profiles = list_profiles(vault.path)
    assert "dev" in profiles
    assert "prod" in profiles


def test_define_profile_empty_name_raises(vault):
    with pytest.raises(ProfileError, match="empty"):
        define_profile(vault.path, "", ["DB_HOST"])


def test_define_profile_empty_keys_raises(vault):
    with pytest.raises(ProfileError, match="at least one key"):
        define_profile(vault.path, "dev", [])


def test_get_profile_keys_returns_correct_keys(vault):
    define_profile(vault.path, "staging", ["DB_HOST", "REDIS_URL"])
    keys = get_profile_keys(vault.path, "staging")
    assert keys == ["DB_HOST", "REDIS_URL"]


def test_get_profile_missing_raises(vault):
    with pytest.raises(ProfileError, match="does not exist"):
        get_profile_keys(vault.path, "nonexistent")


def test_delete_profile_removes_it(vault):
    define_profile(vault.path, "temp", ["API_KEY"])
    delete_profile(vault.path, "temp")
    assert "temp" not in list_profiles(vault.path)


def test_delete_missing_profile_raises(vault):
    with pytest.raises(ProfileError, match="does not exist"):
        delete_profile(vault.path, "ghost")


def test_apply_profile_returns_matching_values(vault):
    define_profile(vault.path, "db", ["DB_HOST", "DB_PORT"])
    result = apply_profile(vault.path, "db", vault)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432"}


def test_apply_profile_skips_missing_vault_keys(vault):
    define_profile(vault.path, "partial", ["DB_HOST", "MISSING_KEY"])
    result = apply_profile(vault.path, "partial", vault)
    assert "DB_HOST" in result
    assert "MISSING_KEY" not in result


def test_list_profiles_empty_when_none_defined(vault):
    assert list_profiles(vault.path) == []


def test_define_profile_overwrites_existing(vault):
    define_profile(vault.path, "env", ["DB_HOST"])
    define_profile(vault.path, "env", ["API_KEY", "REDIS_URL"])
    keys = get_profile_keys(vault.path, "env")
    assert keys == ["API_KEY", "REDIS_URL"]
