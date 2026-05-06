"""Backup and restore vault files to/from a compressed archive."""

import gzip
import json
import os
import shutil
import time
from pathlib import Path

from envault.vault import Vault, VaultError


class BackupError(Exception):
    """Raised when a backup or restore operation fails."""


def create_backup(vault: Vault, backup_path: str) -> str:
    """Create a compressed backup of the vault file.

    Args:
        vault: An open Vault instance.
        backup_path: Directory where the backup file will be written.

    Returns:
        The full path to the created backup file.

    Raises:
        BackupError: If the vault file does not exist or backup fails.
    """
    vault_file = Path(vault.path)
    if not vault_file.exists():
        raise BackupError(f"Vault file not found: {vault.path}")

    os.makedirs(backup_path, exist_ok=True)

    timestamp = int(time.time())
    backup_name = f"envault_backup_{timestamp}.json.gz"
    dest = Path(backup_path) / backup_name

    try:
        with vault_file.open("rb") as src, gzip.open(dest, "wb") as gz:
            shutil.copyfileobj(src, gz)
    except OSError as exc:
        raise BackupError(f"Failed to write backup: {exc}") from exc

    return str(dest)


def restore_backup(backup_file: str, vault_path: str, password: str) -> int:
    """Restore a vault from a compressed backup file.

    Args:
        backup_file: Path to the .json.gz backup file.
        vault_path: Destination path for the restored vault file.
        password: Password used to verify the restored vault is readable.

    Returns:
        Number of secrets restored.

    Raises:
        BackupError: If the backup file is missing, corrupt, or the password
                     does not open the restored vault.
    """
    src = Path(backup_file)
    if not src.exists():
        raise BackupError(f"Backup file not found: {backup_file}")

    dest = Path(vault_path)

    try:
        with gzip.open(src, "rb") as gz, dest.open("wb") as out:
            shutil.copyfileobj(gz, out)
    except (OSError, gzip.BadGzipFile) as exc:
        raise BackupError(f"Failed to decompress backup: {exc}") from exc

    try:
        vault = Vault(vault_path, password)
        return len(vault.list())
    except VaultError as exc:
        dest.unlink(missing_ok=True)
        raise BackupError(f"Restored vault could not be opened: {exc}") from exc
