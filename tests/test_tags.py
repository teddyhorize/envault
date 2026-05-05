"""Tests for envault.tags module."""

import pytest

from envault.vault import Vault
from envault.tags import (
    TagsError,
    add_tag,
    remove_tag,
    get_tags,
    keys_by_tag,
    all_tags,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="secret")
    v.set("DB_URL", "postgres://localhost/db")
    v.set("API_KEY", "abc123")
    v.set("REDIS_URL", "redis://localhost")
    return v


def test_add_tag_and_get_tags(vault):
    add_tag(vault, "DB_URL", "database")
    assert "database" in get_tags(vault, "DB_URL")


def test_add_multiple_tags_to_same_key(vault):
    add_tag(vault, "DB_URL", "database")
    add_tag(vault, "DB_URL", "production")
    tags = get_tags(vault, "DB_URL")
    assert "database" in tags
    assert "production" in tags


def test_add_duplicate_tag_is_idempotent(vault):
    add_tag(vault, "API_KEY", "external")
    add_tag(vault, "API_KEY", "external")
    assert get_tags(vault, "API_KEY").count("external") == 1


def test_add_tag_missing_key_raises(vault):
    with pytest.raises(TagsError, match="does not exist"):
        add_tag(vault, "NONEXISTENT", "sometag")


def test_add_tag_empty_key_raises(vault):
    with pytest.raises(TagsError, match="must not be empty"):
        add_tag(vault, "", "sometag")


def test_add_tag_empty_tag_raises(vault):
    with pytest.raises(TagsError, match="must not be empty"):
        add_tag(vault, "DB_URL", "")


def test_remove_tag_returns_true_when_present(vault):
    add_tag(vault, "API_KEY", "external")
    result = remove_tag(vault, "API_KEY", "external")
    assert result is True
    assert "external" not in get_tags(vault, "API_KEY")


def test_remove_tag_returns_false_when_absent(vault):
    result = remove_tag(vault, "API_KEY", "ghost")
    assert result is False


def test_keys_by_tag_returns_correct_keys(vault):
    add_tag(vault, "DB_URL", "infra")
    add_tag(vault, "REDIS_URL", "infra")
    add_tag(vault, "API_KEY", "external")
    keys = keys_by_tag(vault, "infra")
    assert set(keys) == {"DB_URL", "REDIS_URL"}


def test_keys_by_tag_empty_when_no_matches(vault):
    assert keys_by_tag(vault, "nonexistent-tag") == []


def test_all_tags_returns_full_mapping(vault):
    add_tag(vault, "DB_URL", "database")
    add_tag(vault, "API_KEY", "external")
    mapping = all_tags(vault)
    assert mapping["DB_URL"] == ["database"]
    assert mapping["API_KEY"] == ["external"]


def test_get_tags_no_tags_returns_empty(vault):
    assert get_tags(vault, "DB_URL") == []
