"""Tests for envault.history module."""
import time
import pytest

from envault.vault import Vault
from envault.history import (
    HistoryError,
    record_version,
    get_versions,
    get_latest_version,
    clear_history,
    _history_path,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="secret")
    v.set("API_KEY", "initial")
    v.set("DB_PASS", "pass1")
    return v


def test_record_version_creates_entry(vault):
    record_version(vault, "API_KEY", "v1")
    versions = get_versions(vault, "API_KEY")
    assert len(versions) == 1
    assert versions[0]["value"] == "v1"


def test_record_multiple_versions(vault):
    record_version(vault, "API_KEY", "v1")
    record_version(vault, "API_KEY", "v2")
    record_version(vault, "API_KEY", "v3")
    versions = get_versions(vault, "API_KEY")
    assert len(versions) == 3
    assert [e["value"] for e in versions] == ["v1", "v2", "v3"]


def test_entry_has_timestamp(vault):
    before = time.time()
    record_version(vault, "API_KEY", "v1")
    after = time.time()
    entry = get_versions(vault, "API_KEY")[0]
    assert before <= entry["timestamp"] <= after


def test_get_versions_empty_when_no_history(vault):
    versions = get_versions(vault, "API_KEY")
    assert versions == []


def test_get_latest_version_returns_last(vault):
    record_version(vault, "API_KEY", "v1")
    record_version(vault, "API_KEY", "v2")
    latest = get_latest_version(vault, "API_KEY")
    assert latest["value"] == "v2"


def test_get_latest_version_none_when_empty(vault):
    assert get_latest_version(vault, "API_KEY") is None


def test_clear_history_removes_entries(vault):
    record_version(vault, "API_KEY", "v1")
    record_version(vault, "API_KEY", "v2")
    removed = clear_history(vault, "API_KEY")
    assert removed == 2
    assert get_versions(vault, "API_KEY") == []


def test_clear_history_returns_zero_when_empty(vault):
    assert clear_history(vault, "API_KEY") == 0


def test_record_empty_key_raises(vault):
    with pytest.raises(HistoryError):
        record_version(vault, "", "val")


def test_get_versions_empty_key_raises(vault):
    with pytest.raises(HistoryError):
        get_versions(vault, "")


def test_history_file_created_on_first_record(vault, tmp_path):
    assert not _history_path(vault).exists()
    record_version(vault, "API_KEY", "v1")
    assert _history_path(vault).exists()


def test_independent_keys_have_independent_histories(vault):
    record_version(vault, "API_KEY", "a1")
    record_version(vault, "DB_PASS", "b1")
    record_version(vault, "DB_PASS", "b2")
    assert len(get_versions(vault, "API_KEY")) == 1
    assert len(get_versions(vault, "DB_PASS")) == 2
