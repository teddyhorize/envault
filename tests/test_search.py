"""Tests for envault.search module."""

import pytest

from envault.vault import Vault
from envault.tags import add_tag
from envault.search import SearchError, search_by_pattern, search_by_tag


PASSWORD = "test-password"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.json"), PASSWORD)
    v.set("DB_HOST", "localhost", PASSWORD)
    v.set("DB_PORT", "5432", PASSWORD)
    v.set("API_KEY", "abc123", PASSWORD)
    v.set("API_SECRET", "supersecret", PASSWORD)
    v.set("UNRELATED", "value", PASSWORD)
    return v


# --- search_by_pattern ---

def test_pattern_matches_prefix(vault):
    results = search_by_pattern(vault, "DB_*", PASSWORD)
    assert set(results.keys()) == {"DB_HOST", "DB_PORT"}


def test_pattern_matches_substring(vault):
    results = search_by_pattern(vault, "*API*", PASSWORD)
    assert set(results.keys()) == {"API_KEY", "API_SECRET"}


def test_pattern_exact_match(vault):
    results = search_by_pattern(vault, "UNRELATED", PASSWORD)
    assert results == {"UNRELATED": "value"}


def test_pattern_no_match_returns_empty(vault):
    results = search_by_pattern(vault, "MISSING_*", PASSWORD)
    assert results == {}


def test_pattern_returns_correct_values(vault):
    results = search_by_pattern(vault, "DB_HOST", PASSWORD)
    assert results["DB_HOST"] == "localhost"


def test_empty_pattern_raises(vault):
    with pytest.raises(SearchError, match="pattern"):
        search_by_pattern(vault, "", PASSWORD)


# --- search_by_tag ---

def test_search_by_tag_returns_tagged_keys(vault):
    add_tag(vault, "DB_HOST", "database")
    add_tag(vault, "DB_PORT", "database")
    results = search_by_tag(vault, "database", PASSWORD)
    assert set(results.keys()) == {"DB_HOST", "DB_PORT"}


def test_search_by_tag_correct_values(vault):
    add_tag(vault, "API_KEY", "api")
    results = search_by_tag(vault, "api", PASSWORD)
    assert results["API_KEY"] == "abc123"


def test_search_by_tag_no_match_returns_empty(vault):
    results = search_by_tag(vault, "nonexistent-tag", PASSWORD)
    assert results == {}


def test_empty_tag_raises(vault):
    with pytest.raises(SearchError, match="Tag"):
        search_by_tag(vault, "", PASSWORD)
