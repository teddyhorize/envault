"""Tests for envault.env_lock module."""

import time
import pytest
from pathlib import Path
from envault.env_lock import (
    acquire_lock,
    release_lock,
    is_locked,
    get_lock_info,
    LOCK_TIMEOUT_SECONDS,
)


@pytest.fixture
def vault_path(tmp_path):
    p = tmp_path / "test.vault"
    p.write_text("{}")
    return str(p)


def test_acquire_lock_returns_true_when_unlocked(vault_path):
    assert acquire_lock(vault_path) is True


def test_is_locked_after_acquire(vault_path):
    acquire_lock(vault_path)
    assert is_locked(vault_path) is True


def test_is_locked_false_when_no_lock(vault_path):
    assert is_locked(vault_path) is False


def test_release_lock_removes_lock(vault_path):
    acquire_lock(vault_path)
    release_lock(vault_path)
    assert is_locked(vault_path) is False


def test_acquire_fails_when_already_locked(vault_path):
    acquire_lock(vault_path, owner="first")
    result = acquire_lock(vault_path, owner="second")
    assert result is False


def test_get_lock_info_returns_none_when_unlocked(vault_path):
    assert get_lock_info(vault_path) is None


def test_get_lock_info_returns_metadata(vault_path):
    acquire_lock(vault_path, owner="test-owner")
    info = get_lock_info(vault_path)
    assert info is not None
    assert info["owner"] == "test-owner"
    assert "acquired_at" in info
    assert "pid" in info


def test_stale_lock_is_overridden(vault_path):
    acquire_lock(vault_path, owner="stale")
    lock_file = Path(vault_path + ".lock")
    import json
    data = json.loads(lock_file.read_text())
    data["acquired_at"] = time.time() - LOCK_TIMEOUT_SECONDS - 5
    lock_file.write_text(json.dumps(data))

    result = acquire_lock(vault_path, owner="fresh")
    assert result is True
    info = get_lock_info(vault_path)
    assert info["owner"] == "fresh"


def test_release_lock_is_idempotent(vault_path):
    release_lock(vault_path)
    release_lock(vault_path)  # Should not raise
    assert is_locked(vault_path) is False
