"""Tests for envault.env_schedule."""

import time
import pytest

from envault.vault import Vault
from envault.env_schedule import (
    ScheduleError,
    schedule_rotation,
    remove_schedule,
    get_schedule,
    list_schedules,
    due_keys,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="secret")
    v.set("API_KEY", "abc123")
    v.set("DB_PASS", "hunter2")
    return v


def test_schedule_rotation_returns_future_timestamp(vault):
    next_due = schedule_rotation(vault, "API_KEY", 3600)
    assert next_due > time.time()


def test_schedule_rotation_stores_interval(vault):
    schedule_rotation(vault, "API_KEY", 3600)
    info = get_schedule(vault, "API_KEY")
    assert info is not None
    assert info["interval"] == 3600


def test_schedule_rotation_missing_key_raises(vault):
    with pytest.raises(ScheduleError, match="does not exist"):
        schedule_rotation(vault, "NONEXISTENT", 60)


def test_schedule_rotation_empty_key_raises(vault):
    with pytest.raises(ScheduleError, match="must not be empty"):
        schedule_rotation(vault, "", 60)


def test_schedule_rotation_zero_interval_raises(vault):
    with pytest.raises(ScheduleError, match="positive integer"):
        schedule_rotation(vault, "API_KEY", 0)


def test_schedule_rotation_negative_interval_raises(vault):
    with pytest.raises(ScheduleError, match="positive integer"):
        schedule_rotation(vault, "API_KEY", -10)


def test_get_schedule_not_set_returns_none(vault):
    assert get_schedule(vault, "API_KEY") is None


def test_remove_schedule(vault):
    schedule_rotation(vault, "API_KEY", 3600)
    remove_schedule(vault, "API_KEY")
    assert get_schedule(vault, "API_KEY") is None


def test_remove_schedule_nonexistent_raises(vault):
    with pytest.raises(ScheduleError, match="No schedule found"):
        remove_schedule(vault, "API_KEY")


def test_list_schedules_empty_initially(vault):
    assert list_schedules(vault) == []


def test_list_schedules_returns_all(vault):
    schedule_rotation(vault, "API_KEY", 3600)
    schedule_rotation(vault, "DB_PASS", 7200)
    result = list_schedules(vault)
    keys = [r["key"] for r in result]
    assert "API_KEY" in keys
    assert "DB_PASS" in keys


def test_due_keys_empty_when_not_due(vault):
    schedule_rotation(vault, "API_KEY", 9999)
    assert due_keys(vault) == []


def test_due_keys_returns_overdue_key(vault):
    schedule_rotation(vault, "API_KEY", -1)  # already past
    # Manually force next_due into the past by re-scheduling with tiny interval
    import json
    from pathlib import Path
    p = Path(vault.path).with_suffix(".schedule.json")
    data = json.loads(p.read_text())
    data["API_KEY"]["next_due"] = time.time() - 1
    p.write_text(json.dumps(data))
    assert "API_KEY" in due_keys(vault)
