"""Tests for envault.cli_group module."""

import argparse
import pytest
from pathlib import Path

from envault.vault import Vault
from envault.cli_group import (
    cmd_group_define,
    cmd_group_delete,
    cmd_group_list,
    cmd_group_show,
)


@pytest.fixture
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="pass")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "abc123")
    return v


def _make_args(vault_path, password, **kwargs):
    ns = argparse.Namespace(vault=vault_path, password=password, **kwargs)
    return ns


def test_define_prints_confirmation(src_vault, capsys):
    args = _make_args(src_vault.path, "pass", name="db", keys=["DB_HOST", "DB_PORT"])
    cmd_group_define(args)
    out = capsys.readouterr().out
    assert "db" in out
    assert "DB_HOST" in out


def test_define_missing_key_exits(src_vault):
    args = _make_args(src_vault.path, "pass", name="bad", keys=["MISSING"])
    with pytest.raises(SystemExit):
        cmd_group_define(args)


def test_define_empty_name_exits(src_vault):
    args = _make_args(src_vault.path, "pass", name="", keys=["DB_HOST"])
    with pytest.raises(SystemExit):
        cmd_group_define(args)


def test_list_prints_groups(src_vault, capsys):
    from envault.env_group import define_group
    define_group(src_vault, "db", ["DB_HOST", "DB_PORT"])
    args = _make_args(src_vault.path, "pass")
    cmd_group_list(args)
    out = capsys.readouterr().out
    assert "db" in out
    assert "DB_HOST" in out


def test_list_empty_prints_message(src_vault, capsys):
    args = _make_args(src_vault.path, "pass")
    cmd_group_list(args)
    out = capsys.readouterr().out
    assert "No groups" in out


def test_delete_prints_confirmation(src_vault, capsys):
    from envault.env_group import define_group
    define_group(src_vault, "db", ["DB_HOST"])
    args = _make_args(src_vault.path, "pass", name="db")
    cmd_group_delete(args)
    out = capsys.readouterr().out
    assert "deleted" in out


def test_delete_nonexistent_exits(src_vault):
    args = _make_args(src_vault.path, "pass", name="ghost")
    with pytest.raises(SystemExit):
        cmd_group_delete(args)


def test_show_prints_key_values(src_vault, capsys):
    from envault.env_group import define_group
    define_group(src_vault, "db", ["DB_HOST", "DB_PORT"])
    args = _make_args(src_vault.path, "pass", name="db")
    cmd_group_show(args)
    out = capsys.readouterr().out
    assert "DB_HOST=localhost" in out
    assert "DB_PORT=5432" in out


def test_show_nonexistent_group_exits(src_vault):
    args = _make_args(src_vault.path, "pass", name="ghost")
    with pytest.raises(SystemExit):
        cmd_group_show(args)
