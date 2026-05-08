"""Tests for envault.env_clone."""

from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.env_clone import CloneError, clone_vault


SRC_PASS = "src-password"
DST_PASS = "dst-password"


@pytest.fixture()
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "src.vault"))
    v.set("DB_HOST", "localhost", SRC_PASS)
    v.set("DB_PORT", "5432", SRC_PASS)
    v.set("API_KEY", "secret-key", SRC_PASS)
    return v


@pytest.fixture()
def dst_vault(tmp_path):
    return Vault(str(tmp_path / "dst.vault"))


def test_clone_all_keys(src_vault, dst_vault):
    written = clone_vault(src_vault, SRC_PASS, dst_vault, DST_PASS)
    assert set(written) == {"DB_HOST", "DB_PORT", "API_KEY"}
    assert dst_vault.get("DB_HOST", DST_PASS) == "localhost"
    assert dst_vault.get("API_KEY", DST_PASS) == "secret-key"


def test_clone_subset_of_keys(src_vault, dst_vault):
    written = clone_vault(src_vault, SRC_PASS, dst_vault, DST_PASS, keys=["DB_HOST"])
    assert written == ["DB_HOST"]
    assert dst_vault.get("DB_HOST", DST_PASS) == "localhost"
    assert dst_vault.get("API_KEY", DST_PASS) is None


def test_clone_missing_key_raises(src_vault, dst_vault):
    with pytest.raises(CloneError, match="not found in source vault"):
        clone_vault(src_vault, SRC_PASS, dst_vault, DST_PASS, keys=["NONEXISTENT"])


def test_clone_empty_source_raises(tmp_path, dst_vault):
    empty = Vault(str(tmp_path / "empty.vault"))
    with pytest.raises(CloneError, match="empty"):
        clone_vault(empty, SRC_PASS, dst_vault, DST_PASS)


def test_clone_no_overwrite_skips_existing(src_vault, dst_vault):
    dst_vault.set("DB_HOST", "existing-value", DST_PASS)
    written = clone_vault(
        src_vault, SRC_PASS, dst_vault, DST_PASS,
        keys=["DB_HOST", "DB_PORT"],
        overwrite=False,
    )
    assert "DB_HOST" not in written
    assert "DB_PORT" in written
    # Original value preserved
    assert dst_vault.get("DB_HOST", DST_PASS) == "existing-value"


def test_clone_overwrite_replaces_existing(src_vault, dst_vault):
    dst_vault.set("DB_HOST", "old-value", DST_PASS)
    clone_vault(src_vault, SRC_PASS, dst_vault, DST_PASS, overwrite=True)
    assert dst_vault.get("DB_HOST", DST_PASS) == "localhost"


def test_clone_returns_written_key_names(src_vault, dst_vault):
    written = clone_vault(src_vault, SRC_PASS, dst_vault, DST_PASS)
    assert isinstance(written, list)
    assert len(written) == 3
