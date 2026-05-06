"""Tests for envault.backup module."""

import gzip
import os
import pytest

from envault.vault import Vault
from envault.backup import BackupError, create_backup, restore_backup


PASSWORD = "test-backup-password"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.json"), PASSWORD)
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "secret-key-123")
    return v


@pytest.fixture()
def backup_dir(tmp_path):
    return str(tmp_path / "backups")


def test_create_backup_returns_path(vault, backup_dir):
    path = create_backup(vault, backup_dir)
    assert path.endswith(".json.gz")
    assert os.path.exists(path)


def test_create_backup_file_is_valid_gzip(vault, backup_dir):
    path = create_backup(vault, backup_dir)
    with gzip.open(path, "rb") as f:
        content = f.read()
    assert len(content) > 0


def test_create_backup_creates_directory(vault, tmp_path):
    new_dir = str(tmp_path / "nested" / "backups")
    path = create_backup(vault, new_dir)
    assert os.path.exists(path)


def test_create_backup_nonexistent_vault_raises(tmp_path, backup_dir):
    v = Vault(str(tmp_path / "ghost.json"), PASSWORD)
    with pytest.raises(BackupError, match="Vault file not found"):
        create_backup(v, backup_dir)


def test_restore_backup_returns_secret_count(vault, backup_dir, tmp_path):
    backup_path = create_backup(vault, backup_dir)
    restored_path = str(tmp_path / "restored.json")
    count = restore_backup(backup_path, restored_path, PASSWORD)
    assert count == 3


def test_restore_backup_secrets_are_accessible(vault, backup_dir, tmp_path):
    backup_path = create_backup(vault, backup_dir)
    restored_path = str(tmp_path / "restored.json")
    restore_backup(backup_path, restored_path, PASSWORD)
    restored_vault = Vault(restored_path, PASSWORD)
    assert restored_vault.get("DB_HOST") == "localhost"
    assert restored_vault.get("API_KEY") == "secret-key-123"


def test_restore_backup_wrong_password_raises(vault, backup_dir, tmp_path):
    backup_path = create_backup(vault, backup_dir)
    restored_path = str(tmp_path / "restored.json")
    with pytest.raises(BackupError, match="could not be opened"):
        restore_backup(backup_path, restored_path, "wrong-password")


def test_restore_backup_missing_file_raises(tmp_path):
    with pytest.raises(BackupError, match="Backup file not found"):
        restore_backup(str(tmp_path / "no_such.json.gz"), str(tmp_path / "v.json"), PASSWORD)


def test_restore_backup_corrupt_file_raises(tmp_path):
    bad_file = tmp_path / "corrupt.json.gz"
    bad_file.write_bytes(b"not gzip data at all")
    with pytest.raises(BackupError, match="Failed to decompress"):
        restore_backup(str(bad_file), str(tmp_path / "v.json"), PASSWORD)
