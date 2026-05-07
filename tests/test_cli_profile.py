"""Tests for envault/cli_profile.py"""

import pytest
from unittest.mock import patch
from pathlib import Path
from envault.vault import Vault
from envault.env_profile import define_profile
from envault.cli_profile import (
    cmd_profile_define,
    cmd_profile_delete,
    cmd_profile_list,
    cmd_profile_apply,
)


@pytest.fixture
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "vault.enc"), password="pass")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "secret")
    return v


def _make_args(vault, **kwargs):
    class Args:
        pass
    a = Args()
    a.vault = vault.path
    a.password = "pass"
    for k, v in kwargs.items():
        setattr(a, k, v)
    return a


def test_define_prints_confirmation(src_vault, capsys):
    args = _make_args(src_vault, name="dev", keys="DB_HOST,DB_PORT")
    cmd_profile_define(args)
    out = capsys.readouterr().out
    assert "dev" in out
    assert "2 key(s)" in out


def test_define_empty_name_exits(src_vault):
    args = _make_args(src_vault, name="", keys="DB_HOST")
    with pytest.raises(SystemExit):
        cmd_profile_define(args)


def test_define_empty_keys_exits(src_vault):
    args = _make_args(src_vault, name="dev", keys="  ,  ")
    with pytest.raises(SystemExit):
        cmd_profile_define(args)


def test_list_shows_profiles(src_vault, capsys):
    define_profile(src_vault.path, "prod", ["API_KEY"])
    args = _make_args(src_vault)
    cmd_profile_list(args)
    out = capsys.readouterr().out
    assert "prod" in out
    assert "API_KEY" in out


def test_list_empty_message(src_vault, capsys):
    args = _make_args(src_vault)
    cmd_profile_list(args)
    out = capsys.readouterr().out
    assert "No profiles" in out


def test_delete_prints_confirmation(src_vault, capsys):
    define_profile(src_vault.path, "temp", ["DB_HOST"])
    args = _make_args(src_vault, name="temp")
    cmd_profile_delete(args)
    out = capsys.readouterr().out
    assert "deleted" in out


def test_delete_missing_profile_exits(src_vault):
    args = _make_args(src_vault, name="ghost")
    with pytest.raises(SystemExit):
        cmd_profile_delete(args)


def test_apply_prints_key_values(src_vault, capsys):
    define_profile(src_vault.path, "db", ["DB_HOST", "DB_PORT"])
    args = _make_args(src_vault, name="db")
    cmd_profile_apply(args)
    out = capsys.readouterr().out
    assert "DB_HOST=localhost" in out
    assert "DB_PORT=5432" in out


def test_apply_missing_profile_exits(src_vault):
    args = _make_args(src_vault, name="nonexistent")
    with pytest.raises(SystemExit):
        cmd_profile_apply(args)
