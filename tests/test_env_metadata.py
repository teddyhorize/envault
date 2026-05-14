"""Tests for envault.env_metadata."""

import pytest

from envault.vault import Vault
from envault.env_metadata import (
    MetadataError,
    set_metadata,
    get_metadata,
    get_all_metadata,
    remove_metadata,
    clear_metadata,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="pass")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    return v


def test_set_and_get_metadata(vault):
    set_metadata(vault, "DB_HOST", "owner", "alice")
    assert get_metadata(vault, "DB_HOST", "owner") == "alice"


def test_get_metadata_not_set_returns_none(vault):
    assert get_metadata(vault, "DB_HOST", "owner") is None


def test_set_multiple_fields_on_same_key(vault):
    set_metadata(vault, "DB_HOST", "owner", "alice")
    set_metadata(vault, "DB_HOST", "env", "production")
    assert get_metadata(vault, "DB_HOST", "owner") == "alice"
    assert get_metadata(vault, "DB_HOST", "env") == "production"


def test_get_all_metadata_returns_all_fields(vault):
    set_metadata(vault, "DB_HOST", "owner", "bob")
    set_metadata(vault, "DB_HOST", "tier", "free")
    meta = get_all_metadata(vault, "DB_HOST")
    assert meta == {"owner": "bob", "tier": "free"}


def test_get_all_metadata_empty_when_none_set(vault):
    assert get_all_metadata(vault, "DB_HOST") == {}


def test_set_metadata_overwrites_existing_field(vault):
    set_metadata(vault, "DB_HOST", "owner", "alice")
    set_metadata(vault, "DB_HOST", "owner", "charlie")
    assert get_metadata(vault, "DB_HOST", "owner") == "charlie"


def test_set_metadata_missing_key_raises(vault):
    with pytest.raises(MetadataError, match="does not exist"):
        set_metadata(vault, "MISSING", "owner", "alice")


def test_set_metadata_empty_key_raises(vault):
    with pytest.raises(MetadataError, match="must not be empty"):
        set_metadata(vault, "", "owner", "alice")


def test_set_metadata_empty_field_raises(vault):
    with pytest.raises(MetadataError, match="field name must not be empty"):
        set_metadata(vault, "DB_HOST", "", "value")


def test_remove_metadata_returns_true_when_existed(vault):
    set_metadata(vault, "DB_HOST", "owner", "alice")
    result = remove_metadata(vault, "DB_HOST", "owner")
    assert result is True
    assert get_metadata(vault, "DB_HOST", "owner") is None


def test_remove_metadata_returns_false_when_not_set(vault):
    result = remove_metadata(vault, "DB_HOST", "nonexistent")
    assert result is False


def test_clear_metadata_removes_all_fields(vault):
    set_metadata(vault, "DB_HOST", "owner", "alice")
    set_metadata(vault, "DB_HOST", "env", "prod")
    clear_metadata(vault, "DB_HOST")
    assert get_all_metadata(vault, "DB_HOST") == {}


def test_metadata_independent_per_key(vault):
    set_metadata(vault, "DB_HOST", "owner", "alice")
    set_metadata(vault, "DB_PORT", "owner", "bob")
    assert get_metadata(vault, "DB_HOST", "owner") == "alice"
    assert get_metadata(vault, "DB_PORT", "owner") == "bob"
