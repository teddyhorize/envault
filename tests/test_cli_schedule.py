"""Tests for envault.cli_schedule."""

import argparse
import time
import json
from pathlib import Path

import pytest

from envault.vault import Vault
from envault.cli_schedule import (
    cmd_schedule_add,
    cmd_schedule_remove,
    cmd_schedule_list,
    cmd_schedule_due,
)


@pytest.fixture
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="pass")
    v.set("API_KEY", "abc")
    v.set("DB_PASS", "xyz")
    return v


def _make_args(vault, **kwargs):
    ns = argparse.Namespace(vault=vault.path, password="pass", **kwargs)
    return ns


def test_schedule_add_prints_confirmation(src_vault, capsys):
    args = _make_args(src_vault, key="API_KEY", interval=3600)
    cmd_schedule_add(args)
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "3600" in out


def test_schedule_add_missing_key_exits(src_vault):
    args = _make_args(src_vault, key="MISSING", interval=60)
    with pytest.raises(SystemExit):
        cmd_schedule_add(args)


def test_schedule_add_bad_password_exits(src_vault):
    ns = argparse.Namespace(vault=src_vault.path, password="wrong", key="API_KEY", interval=60)
    with pytest.raises(SystemExit):
        cmd_schedule_add(ns)


def test_schedule_remove_prints_confirmation(src_vault, capsys):
    add_args = _make_args(src_vault, key="API_KEY", interval=3600)
    cmd_schedule_add(add_args)
    rem_args = _make_args(src_vault, key="API_KEY")
    cmd_schedule_remove(rem_args)
    out = capsys.readouterr().out
    assert "Removed" in out


def test_schedule_remove_nonexistent_exits(src_vault):
    args = _make_args(src_vault, key="API_KEY")
    with pytest.raises(SystemExit):
        cmd_schedule_remove(args)


def test_schedule_list_empty_message(src_vault, capsys):
    args = _make_args(src_vault)
    cmd_schedule_list(args)
    out = capsys.readouterr().out
    assert "No rotation schedules" in out


def test_schedule_list_shows_entries(src_vault, capsys):
    cmd_schedule_add(_make_args(src_vault, key="API_KEY", interval=3600))
    cmd_schedule_add(_make_args(src_vault, key="DB_PASS", interval=7200))
    cmd_schedule_list(_make_args(src_vault))
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "DB_PASS" in out


def test_schedule_due_no_due_keys(src_vault, capsys):
    cmd_schedule_add(_make_args(src_vault, key="API_KEY", interval=9999))
    cmd_schedule_due(_make_args(src_vault))
    out = capsys.readouterr().out
    assert "No keys" in out


def test_schedule_due_shows_overdue_key(src_vault, capsys):
    cmd_schedule_add(_make_args(src_vault, key="API_KEY", interval=3600))
    p = Path(src_vault.path).with_suffix(".schedule.json")
    data = json.loads(p.read_text())
    data["API_KEY"]["next_due"] = time.time() - 10
    p.write_text(json.dumps(data))
    cmd_schedule_due(_make_args(src_vault))
    out = capsys.readouterr().out
    assert "API_KEY" in out
