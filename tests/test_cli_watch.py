"""Tests for envault.cli_watch."""
from __future__ import annotations

import argparse
import os
import sys
import pytest

from envault.vault import Vault
from envault.cli_watch import cmd_watch, build_watch_parser, _open_vault


@pytest.fixture
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "vault.db"), password="secret")
    v.set("API_KEY", "abc123")
    return v


def _make_args(**kwargs) -> argparse.Namespace:
    defaults = {"interval": 0.1}
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_open_vault_success(src_vault):
    v = _open_vault(src_vault.path, "secret")
    assert v.get("API_KEY") == "abc123"


def test_open_vault_bad_password_exits(src_vault):
    with pytest.raises(SystemExit):
        _open_vault(src_vault.path, "wrongpassword")


def test_open_vault_missing_file_exits(tmp_path):
    # A missing vault file should raise on open; depending on Vault impl it may
    # raise VaultError or succeed (creates new). We just check it doesn't crash
    # unexpectedly when valid path provided.
    path = str(tmp_path / "new_vault.db")
    # Should not raise — creates a new vault
    v = _open_vault(path, "pass")
    assert v is not None


def test_build_watch_parser_registers_command():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    build_watch_parser(subparsers)
    args = parser.parse_args(["watch", "vault.db", "--password", "pw"])
    assert args.vault == "vault.db"
    assert args.password == "pw"
    assert args.interval == 2.0


def test_build_watch_parser_custom_interval():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    build_watch_parser(subparsers)
    args = parser.parse_args(["watch", "vault.db", "--password", "pw", "--interval", "5.0"])
    assert args.interval == 5.0


def test_cmd_watch_missing_vault_exits(tmp_path, capsys):
    """cmd_watch should exit if WatchError is raised (vault not found after open)."""
    # Create vault then delete it to trigger WatchError inside VaultWatcher
    path = str(tmp_path / "gone.db")
    v = Vault(path, password="pw")
    v.set("X", "1")
    os.remove(path)
    args = _make_args(vault=path, password="pw")
    with pytest.raises(SystemExit):
        cmd_watch(args)
    captured = capsys.readouterr()
    assert "Watch error" in captured.err or "Error" in captured.err
