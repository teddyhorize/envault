"""Vault locking mechanism to prevent concurrent writes."""

import json
import os
import time
from pathlib import Path

LOCK_FILE_SUFFIX = ".lock"
LOCK_TIMEOUT_SECONDS = 30


class LockError(Exception):
    """Raised when a vault lock operation fails."""


def _lock_path(vault_path: str) -> Path:
    return Path(vault_path + LOCK_FILE_SUFFIX)


def acquire_lock(vault_path: str, owner: str = "envault") -> bool:
    """Acquire an exclusive lock on the vault. Returns True if acquired."""
    lock_file = _lock_path(vault_path)
    now = time.time()

    if lock_file.exists():
        try:
            data = json.loads(lock_file.read_text())
            acquired_at = data.get("acquired_at", 0)
            if now - acquired_at < LOCK_TIMEOUT_SECONDS:
                return False
            # Stale lock — remove it
            lock_file.unlink()
        except (json.JSONDecodeError, OSError):
            lock_file.unlink(missing_ok=True)

    lock_data = {"owner": owner, "acquired_at": now, "pid": os.getpid()}
    lock_file.write_text(json.dumps(lock_data))
    return True


def release_lock(vault_path: str) -> None:
    """Release the lock on the vault."""
    lock_file = _lock_path(vault_path)
    lock_file.unlink(missing_ok=True)


def is_locked(vault_path: str) -> bool:
    """Return True if the vault is currently locked (and lock is not stale)."""
    lock_file = _lock_path(vault_path)
    if not lock_file.exists():
        return False
    try:
        data = json.loads(lock_file.read_text())
        acquired_at = data.get("acquired_at", 0)
        return (time.time() - acquired_at) < LOCK_TIMEOUT_SECONDS
    except (json.JSONDecodeError, OSError):
        return False


def get_lock_info(vault_path: str) -> dict | None:
    """Return lock metadata dict, or None if not locked."""
    if not is_locked(vault_path):
        return None
    lock_file = _lock_path(vault_path)
    try:
        return json.loads(lock_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def wait_for_lock(vault_path: str, owner: str = "envault", timeout: float = LOCK_TIMEOUT_SECONDS, poll_interval: float = 0.1) -> bool:
    """Poll until the lock is acquired or the timeout is exceeded.

    Args:
        vault_path: Path to the vault file.
        owner: Identifier for the lock owner.
        timeout: Maximum seconds to wait before giving up.
        poll_interval: Seconds to sleep between acquisition attempts.

    Returns:
        True if the lock was acquired within the timeout, False otherwise.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if acquire_lock(vault_path, owner=owner):
            return True
        time.sleep(poll_interval)
    return False
