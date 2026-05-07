"""Tests for envault.snapshot module."""

import json
import pytest

from envault.vault import Vault
from envault.snapshot import SnapshotError, create_snapshot, restore_snapshot


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="s3cret")
    v.set("DB_URL", "postgres://localhost/mydb")
    v.set("API_KEY", "abc123")
    v.set("SECRET_TOKEN", "tok_xyz")
    return v


@pytest.fixture
def empty_vault(tmp_path):
    return Vault(str(tmp_path / "empty.vault"), password="s3cret")


def test_create_snapshot_returns_string(vault):
    result = create_snapshot(vault)
    assert isinstance(result, str)


def test_create_snapshot_contains_all_keys(vault):
    result = create_snapshot(vault)
    payload = json.loads(result)
    assert "DB_URL" in payload["secrets"]
    assert "API_KEY" in payload["secrets"]
    assert "SECRET_TOKEN" in payload["secrets"]


def test_create_snapshot_contains_correct_values(vault):
    result = create_snapshot(vault)
    payload = json.loads(result)
    assert payload["secrets"]["DB_URL"] == "postgres://localhost/mydb"
    assert payload["secrets"]["API_KEY"] == "abc123"


def test_create_snapshot_has_timestamp(vault):
    result = create_snapshot(vault)
    payload = json.loads(result)
    assert "created_at" in payload
    assert isinstance(payload["created_at"], float)


def test_create_snapshot_timestamp_is_recent(vault):
    """Ensure the snapshot timestamp reflects the current time."""
    import time

    before = time.time()
    result = create_snapshot(vault)
    after = time.time()
    payload = json.loads(result)
    assert before <= payload["created_at"] <= after


def test_create_snapshot_empty_vault_raises(empty_vault):
    with pytest.raises(SnapshotError, match="empty"):
        create_snapshot(empty_vault)


def test_restore_snapshot_writes_secrets(vault, tmp_path):
    snap = create_snapshot(vault)
    target = Vault(str(tmp_path / "target.vault"), password="other")
    written = restore_snapshot(target, snap)
    assert written == 3
    assert target.get("DB_URL") == "postgres://localhost/mydb"


def test_restore_snapshot_skips_existing_keys_by_default(vault, tmp_path):
    snap = create_snapshot(vault)
    target = Vault(str(tmp_path / "target2.vault"), password="other")
    target.set("DB_URL", "original_value")
    written = restore_snapshot(target, snap)
    assert written == 2
    assert target.get("DB_URL") == "original_value"


def test_restore_snapshot_overwrite_replaces_existing(vault, tmp_path):
    snap = create_snapshot(vault)
    target = Vault(str(tmp_path / "target3.vault"), password="other")
    target.set("DB_URL", "original_value")
    written = restore_snapshot(target, snap, overwrite=True)
    assert written == 3
    assert target.get("DB_URL") == "postgres://localhost/mydb"


def test_restore_snapshot_invalid_json_raises(empty_vault):
    with pytest.raises(SnapshotError, match="Invalid snapshot"):
        restore_snapshot(empty_vault, "not valid json{{")


def test_restore_snapshot_missing_secrets_field_raises(empty_vault):
    bad = json.dumps({"created_at": 1234567890.0})
    with pytest.raises(SnapshotError, match="Invalid snapshot"):
        restore_snapshot(empty_vault, bad)
