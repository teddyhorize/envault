"""Tests for envault.cli_diff module."""

import argparse
import pytest
from unittest.mock import patch, MagicMock
from envault.vault import Vault
from envault.cli_diff import cmd_diff, build_diff_parser


PASSWORD = "cli-diff-pass"


@pytest.fixture
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "src.vault"), PASSWORD)
    v.set("ALPHA", "aaa", PASSWORD)
    v.set("BETA", "bbb", PASSWORD)
    return str(tmp_path / "src.vault")


@pytest.fixture
def dst_vault(tmp_path):
    v = Vault(str(tmp_path / "dst.vault"), PASSWORD)
    v.set("BETA", "bbb_changed", PASSWORD)
    v.set("GAMMA", "ggg", PASSWORD)
    return str(tmp_path / "dst.vault")


def _make_args(left, lp, right, rp):
    ns = argparse.Namespace()
    ns.left_vault = left
    ns.left_password = lp
    ns.right_vault = right
    ns.right_password = rp
    return ns


def test_diff_prints_summary(capsys, src_vault, dst_vault):
    args = _make_args(src_vault, PASSWORD, dst_vault, PASSWORD)
    cmd_diff(args)
    out = capsys.readouterr().out
    assert "+" in out or "-" in out or "~" in out


def test_diff_identical_vaults_prints_identical(capsys, tmp_path):
    v = Vault(str(tmp_path / "v.vault"), PASSWORD)
    v.set("K", "V", PASSWORD)
    path = str(tmp_path / "v.vault")
    args = _make_args(path, PASSWORD, path, PASSWORD)
    cmd_diff(args)
    out = capsys.readouterr().out
    assert "identical" in out.lower()


def test_diff_wrong_password_exits(src_vault, dst_vault):
    args = _make_args(src_vault, "wrong", dst_vault, PASSWORD)
    with pytest.raises(SystemExit) as exc_info:
        cmd_diff(args)
    assert exc_info.value.code == 1


def test_build_diff_parser_registers_subcommand():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    build_diff_parser(subparsers)
    args = parser.parse_args(["diff", "l.vault", "lp", "r.vault", "rp"])
    assert args.left_vault == "l.vault"
    assert args.right_vault == "r.vault"
    assert args.left_password == "lp"
    assert args.right_password == "rp"
