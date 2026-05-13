"""Scheduled secret rotation support for envault."""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

from envault.vault import Vault, VaultError


class ScheduleError(Exception):
    pass


def _schedule_path(vault: Vault) -> Path:
    return Path(vault.path).with_suffix(".schedule.json")


def _load_schedules(vault: Vault) -> Dict[str, dict]:
    p = _schedule_path(vault)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise ScheduleError(f"Failed to load schedules: {exc}") from exc


def _save_schedules(vault: Vault, schedules: Dict[str, dict]) -> None:
    p = _schedule_path(vault)
    try:
        p.write_text(json.dumps(schedules, indent=2))
    except OSError as exc:
        raise ScheduleError(f"Failed to save schedules: {exc}") from exc


def schedule_rotation(vault: Vault, key: str, interval_seconds: int) -> float:
    """Schedule a key for rotation every *interval_seconds* seconds.

    Returns the timestamp of the next due rotation.
    """
    if not key:
        raise ScheduleError("Key must not be empty.")
    if vault.get(key) is None:
        raise ScheduleError(f"Key '{key}' does not exist in vault.")
    if interval_seconds <= 0:
        raise ScheduleError("interval_seconds must be a positive integer.")

    schedules = _load_schedules(vault)
    next_due = time.time() + interval_seconds
    schedules[key] = {"interval": interval_seconds, "next_due": next_due}
    _save_schedules(vault, schedules)
    return next_due


def remove_schedule(vault: Vault, key: str) -> None:
    """Remove the rotation schedule for *key*."""
    schedules = _load_schedules(vault)
    if key not in schedules:
        raise ScheduleError(f"No schedule found for key '{key}'.")
    del schedules[key]
    _save_schedules(vault, schedules)


def get_schedule(vault: Vault, key: str) -> Optional[dict]:
    """Return schedule info for *key*, or None if not scheduled."""
    return _load_schedules(vault).get(key)


def list_schedules(vault: Vault) -> List[dict]:
    """Return all scheduled keys with their metadata."""
    schedules = _load_schedules(vault)
    return [
        {"key": k, "interval": v["interval"], "next_due": v["next_due"]}
        for k, v in schedules.items()
    ]


def due_keys(vault: Vault) -> List[str]:
    """Return keys whose rotation is currently due (next_due <= now)."""
    now = time.time()
    schedules = _load_schedules(vault)
    return [k for k, v in schedules.items() if v["next_due"] <= now]
