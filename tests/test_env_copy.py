"""Tests for envault.env_copy."""
from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.env_copy import CopyError, copy_secret, copy_all


@pytest.fixture()
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "src.vault"), password="src-pass")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "secret-key")
    return v


@pytest.fixture()
def dst_vault(tmp_path):
    return Vault(str(tmp_path / "dst.vault"), password="dst-pass")


# ---------------------------------------------------------------------------
# copy_secret
# ---------------------------------------------------------------------------

def test_copy_secret_copies_value(src_vault, dst_vault):
    copy_secret(src_vault, "DB_HOST", dst_vault)
    assert dst_vault.get("DB_HOST") == "localhost"


def test_copy_secret_with_different_dst_key(src_vault, dst_vault):
    copy_secret(src_vault, "DB_HOST", dst_vault, dst_key="DATABASE_HOST")
    assert dst_vault.get("DATABASE_HOST") == "localhost"
    assert dst_vault.get("DB_HOST") is None


def test_copy_secret_missing_key_raises(src_vault, dst_vault):
    with pytest.raises(CopyError, match="not found"):
        copy_secret(src_vault, "MISSING_KEY", dst_vault)


def test_copy_secret_empty_src_key_raises(src_vault, dst_vault):
    with pytest.raises(CopyError, match="must not be empty"):
        copy_secret(src_vault, "", dst_vault)


def test_copy_secret_empty_dst_key_raises(src_vault, dst_vault):
    with pytest.raises(CopyError, match="must not be empty"):
        copy_secret(src_vault, "DB_HOST", dst_vault, dst_key="   ")


def test_copy_secret_no_overwrite_raises_if_exists(src_vault, dst_vault):
    dst_vault.set("DB_HOST", "other-host")
    with pytest.raises(CopyError, match="already exists"):
        copy_secret(src_vault, "DB_HOST", dst_vault, overwrite=False)


def test_copy_secret_overwrite_replaces_value(src_vault, dst_vault):
    dst_vault.set("DB_HOST", "other-host")
    copy_secret(src_vault, "DB_HOST", dst_vault, overwrite=True)
    assert dst_vault.get("DB_HOST") == "localhost"


def test_copy_secret_within_same_vault(src_vault):
    copy_secret(src_vault, "DB_HOST", src_vault, dst_key="DB_HOST_BACKUP")
    assert src_vault.get("DB_HOST_BACKUP") == "localhost"


# ---------------------------------------------------------------------------
# copy_all
# ---------------------------------------------------------------------------

def test_copy_all_copies_every_key(src_vault, dst_vault):
    copied = copy_all(src_vault, dst_vault)
    assert set(copied) == {"DB_HOST", "DB_PORT", "API_KEY"}
    for key in copied:
        assert dst_vault.get(key) == src_vault.get(key)


def test_copy_all_empty_vault_raises(dst_vault, tmp_path):
    empty = Vault(str(tmp_path / "empty.vault"), password="pass")
    with pytest.raises(CopyError, match="empty"):
        copy_all(empty, dst_vault)


def test_copy_all_returns_list_of_keys(src_vault, dst_vault):
    result = copy_all(src_vault, dst_vault)
    assert isinstance(result, list)
    assert len(result) == 3
