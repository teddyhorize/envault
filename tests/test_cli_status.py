"""Tests for envault.cli_status module."""

import argparse
import pytest

from envault.vault import Vault
from envault.expiry import set_expiry
from envault.env_pin import pin_secret
from envault.cli_status import cmd_status, build_status_parser


@pytest.fixture
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "vault.db"), password="pw")
    v.set("API_KEY", "abc")
    v.set("DB_PASS", "secret")
    return v


def _make_args(vault_path, password="pw", verbose=False):
    return argparse.Namespace(vault=vault_path, password=password, verbose=verbose)


def test_status_prints_summary(src_vault, capsys):
    args = _make_args(src_vault.path)
    cmd_status(args)
    out = capsys.readouterr().out
    assert "Keys" in out
    assert "2" in out


def test_status_verbose_lists_keys(src_vault, capsys):
    args = _make_args(src_vault.path, verbose=True)
    cmd_status(args)
    out = capsys.readouterr().out
    assert "API_KEY" in out
    assert "DB_PASS" in out


def test_status_verbose_shows_pinned(src_vault, capsys):
    pin_secret(src_vault, "API_KEY")
    args = _make_args(src_vault.path, verbose=True)
    cmd_status(args)
    out = capsys.readouterr().out
    assert "pinned" in out


def test_status_verbose_shows_expired(src_vault, capsys):
    set_expiry(src_vault, "DB_PASS", seconds=-1)
    args = _make_args(src_vault.path, verbose=True)
    cmd_status(args)
    out = capsys.readouterr().out
    assert "EXPIRED" in out


def test_status_wrong_password_exits(src_vault):
    args = _make_args(src_vault.path, password="wrong")
    with pytest.raises(SystemExit):
        cmd_status(args)


def test_status_missing_vault_exits(tmp_path):
    args = _make_args(str(tmp_path / "nonexistent.db"))
    with pytest.raises(SystemExit):
        cmd_status(args)


def test_build_status_parser_returns_parser():
    parser = build_status_parser()
    assert isinstance(parser, argparse.ArgumentParser)


def test_build_status_parser_verbose_flag():
    parser = build_status_parser()
    args = parser.parse_args(["--vault", "v.db", "--password", "pw", "--verbose"])
    assert args.verbose is True


def test_status_shows_vault_path(src_vault, capsys):
    args = _make_args(src_vault.path)
    cmd_status(args)
    out = capsys.readouterr().out
    assert src_vault.path in out
