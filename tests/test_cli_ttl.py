"""Tests for envault.cli_ttl."""

import time
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from envault.vault import Vault
from envault.env_ttl import set_ttl
from envault.cli_ttl import (
    cmd_ttl_set,
    cmd_ttl_get,
    cmd_ttl_clear,
    cmd_ttl_list,
    cmd_ttl_purge,
)


@pytest.fixture
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "vault.db"), password="pw")
    v.set("API_KEY", "abc123")
    v.set("DB_PASS", "secret")
    return v


def _make_args(vault: Vault, **kwargs):
    return SimpleNamespace(vault=vault.path, password="pw", **kwargs)


def test_ttl_set_prints_confirmation(src_vault, capsys):
    args = _make_args(src_vault, key="API_KEY", seconds=60)
    cmd_ttl_set(args)
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "60" in out


def test_ttl_set_missing_key_exits(src_vault):
    args = _make_args(src_vault, key="NOPE", seconds=60)
    with pytest.raises(SystemExit):
        cmd_ttl_set(args)


def test_ttl_set_zero_seconds_exits(src_vault):
    args = _make_args(src_vault, key="API_KEY", seconds=0)
    with pytest.raises(SystemExit):
        cmd_ttl_set(args)


def test_ttl_get_no_ttl_set(src_vault, capsys):
    args = _make_args(src_vault, key="API_KEY")
    cmd_ttl_get(args)
    out = capsys.readouterr().out
    assert "No TTL" in out


def test_ttl_get_shows_info(src_vault, capsys):
    set_ttl(src_vault, "API_KEY", 120)
    args = _make_args(src_vault, key="API_KEY")
    cmd_ttl_get(args)
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "120" in out


def test_ttl_get_shows_expired_label(src_vault, capsys):
    set_ttl(src_vault, "API_KEY", 60)
    p = Path(src_vault.path).with_suffix(".ttl.json")
    data = json.loads(p.read_text())
    data["API_KEY"]["expires_at"] = time.time() - 5
    p.write_text(json.dumps(data))
    args = _make_args(src_vault, key="API_KEY")
    cmd_ttl_get(args)
    out = capsys.readouterr().out
    assert "EXPIRED" in out


def test_ttl_clear_removes_ttl(src_vault, capsys):
    set_ttl(src_vault, "API_KEY", 60)
    args = _make_args(src_vault, key="API_KEY")
    cmd_ttl_clear(args)
    out = capsys.readouterr().out
    assert "cleared" in out.lower()


def test_ttl_clear_not_set_message(src_vault, capsys):
    args = _make_args(src_vault, key="API_KEY")
    cmd_ttl_clear(args)
    out = capsys.readouterr().out
    assert "No TTL" in out


def test_ttl_list_empty_message(src_vault, capsys):
    args = _make_args(src_vault)
    cmd_ttl_list(args)
    out = capsys.readouterr().out
    assert "No TTLs" in out


def test_ttl_list_shows_entries(src_vault, capsys):
    set_ttl(src_vault, "API_KEY", 60)
    set_ttl(src_vault, "DB_PASS", 120)
    args = _make_args(src_vault)
    cmd_ttl_list(args)
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "DB_PASS" in out


def test_ttl_purge_no_expired(src_vault, capsys):
    set_ttl(src_vault, "API_KEY", 3600)
    args = _make_args(src_vault)
    cmd_ttl_purge(args)
    out = capsys.readouterr().out
    assert "No expired" in out


def test_ttl_purge_removes_expired(src_vault, capsys):
    set_ttl(src_vault, "API_KEY", 60)
    p = Path(src_vault.path).with_suffix(".ttl.json")
    data = json.loads(p.read_text())
    data["API_KEY"]["expires_at"] = time.time() - 5
    p.write_text(json.dumps(data))
    args = _make_args(src_vault)
    cmd_ttl_purge(args)
    out = capsys.readouterr().out
    assert "API_KEY" in out
