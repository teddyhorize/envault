"""Tests for envault.cli_alias."""

from __future__ import annotations

import argparse
import sys
import pytest

from envault.vault import Vault
from envault.cli_alias import (
    cmd_alias_add,
    cmd_alias_remove,
    cmd_alias_resolve,
    cmd_alias_list,
)


@pytest.fixture
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "vault.db"), password="pw")
    v.set("API_KEY", "abc123")
    v.set("DB_URL", "postgres://localhost/db")
    return v


def _make_args(vault: Vault, **kwargs) -> argparse.Namespace:
    base = {"vault": vault.path, "password": "pw"}
    base.update(kwargs)
    return argparse.Namespace(**base)


def test_alias_add_prints_confirmation(src_vault, capsys):
    args = _make_args(src_vault, alias="key", target="API_KEY")
    cmd_alias_add(args)
    out = capsys.readouterr().out
    assert "key" in out
    assert "API_KEY" in out


def test_alias_add_missing_target_exits(src_vault):
    args = _make_args(src_vault, alias="ghost", target="NO_SUCH_KEY")
    with pytest.raises(SystemExit):
        cmd_alias_add(args)


def test_alias_remove_prints_confirmation(src_vault, capsys):
    from envault.env_alias import add_alias
    add_alias(src_vault, "mykey", "API_KEY")
    args = _make_args(src_vault, alias="mykey")
    cmd_alias_remove(args)
    out = capsys.readouterr().out
    assert "mykey" in out
    assert "removed" in out


def test_alias_remove_nonexistent_exits(src_vault):
    args = _make_args(src_vault, alias="nope")
    with pytest.raises(SystemExit):
        cmd_alias_remove(args)


def test_alias_resolve_prints_value(src_vault, capsys):
    from envault.env_alias import add_alias
    add_alias(src_vault, "the_key", "API_KEY")
    args = _make_args(src_vault, alias="the_key")
    cmd_alias_resolve(args)
    out = capsys.readouterr().out
    assert "abc123" in out


def test_alias_resolve_missing_exits(src_vault):
    args = _make_args(src_vault, alias="undefined")
    with pytest.raises(SystemExit):
        cmd_alias_resolve(args)


def test_alias_list_empty_message(src_vault, capsys):
    args = _make_args(src_vault)
    cmd_alias_list(args)
    out = capsys.readouterr().out
    assert "No aliases" in out


def test_alias_list_shows_entries(src_vault, capsys):
    from envault.env_alias import add_alias
    add_alias(src_vault, "alpha", "API_KEY")
    add_alias(src_vault, "beta", "DB_URL")
    args = _make_args(src_vault)
    cmd_alias_list(args)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out
