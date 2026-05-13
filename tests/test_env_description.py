"""Tests for envault.env_description module."""

import pytest
from pathlib import Path
from envault.vault import Vault
from envault.env_description import (
    DescriptionError,
    set_description,
    get_description,
    remove_description,
    list_descriptions,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="testpass")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "secret-key")
    return v


def test_set_and_get_description(vault):
    set_description(vault, "DB_HOST", "Database hostname")
    assert get_description(vault, "DB_HOST") == "Database hostname"


def test_get_description_not_set_returns_none(vault):
    assert get_description(vault, "DB_HOST") is None


def test_set_description_strips_whitespace(vault):
    set_description(vault, "DB_HOST", "  some description  ")
    assert get_description(vault, "DB_HOST") == "some description"


def test_set_description_missing_key_raises(vault):
    with pytest.raises(DescriptionError, match="does not exist"):
        set_description(vault, "NONEXISTENT", "some description")


def test_set_description_empty_key_raises(vault):
    with pytest.raises(DescriptionError, match="empty"):
        set_description(vault, "", "some description")


def test_get_description_empty_key_raises(vault):
    with pytest.raises(DescriptionError, match="empty"):
        get_description(vault, "")


def test_remove_description_returns_true_when_existed(vault):
    set_description(vault, "DB_PORT", "Database port number")
    result = remove_description(vault, "DB_PORT")
    assert result is True
    assert get_description(vault, "DB_PORT") is None


def test_remove_description_returns_false_when_not_set(vault):
    result = remove_description(vault, "DB_HOST")
    assert result is False


def test_remove_description_empty_key_raises(vault):
    with pytest.raises(DescriptionError, match="empty"):
        remove_description(vault, "")


def test_list_descriptions_returns_all(vault):
    set_description(vault, "DB_HOST", "Host")
    set_description(vault, "API_KEY", "API key for external service")
    descriptions = list_descriptions(vault)
    assert descriptions == {"DB_HOST": "Host", "API_KEY": "API key for external service"}


def test_list_descriptions_empty_when_none_set(vault):
    assert list_descriptions(vault) == {}


def test_overwrite_description(vault):
    set_description(vault, "DB_HOST", "Old description")
    set_description(vault, "DB_HOST", "New description")
    assert get_description(vault, "DB_HOST") == "New description"


def test_descriptions_persisted_across_calls(vault):
    set_description(vault, "DB_HOST", "Persistent description")
    # Re-load by calling list again (same vault object, same file)
    result = list_descriptions(vault)
    assert result["DB_HOST"] == "Persistent description"
