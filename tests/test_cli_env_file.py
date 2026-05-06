"""Tests for envault.cli_env_file."""
from __future__ import annotations

import argparse
from pathlib import Path

import pytest

from envault.vault import Vault
from envault.cli_env_file import cmd_import_env, cmd_export_env


@pytest.fixture()
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "src.db"), password="pw")
    v.set("FOO", "bar")
    v.set("HELLO", "world")
    return v, str(tmp_path / "src.db")


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("FOO=bar\nHELLO=world\n", encoding="utf-8")
    return str(p)


def _make_import_args(vault_path, env_file, password="pw", no_overwrite=False):
    ns = argparse.Namespace(
        vault=vault_path,
        env_file=env_file,
        password=password,
        no_overwrite=no_overwrite,
    )
    return ns


def _make_export_args(vault_path, env_file, password="pw", keys=None):
    ns = argparse.Namespace(
        vault=vault_path,
        env_file=env_file,
        password=password,
        keys=keys or [],
    )
    return ns


# --- import ---

def test_import_prints_imported_count(tmp_path, env_file, capsys):
    v_path = str(tmp_path / "v.db")
    Vault(v_path, password="pw")  # create empty vault
    args = _make_import_args(v_path, env_file)
    cmd_import_env(args)
    out = capsys.readouterr().out
    assert "2 secret(s)" in out


def test_import_wrong_password_exits(tmp_path, env_file):
    v_path = str(tmp_path / "v.db")
    Vault(v_path, password="correct")
    args = _make_import_args(v_path, env_file, password="wrong")
    with pytest.raises(SystemExit):
        cmd_import_env(args)


def test_import_missing_env_file_exits(tmp_path):
    v_path = str(tmp_path / "v.db")
    Vault(v_path, password="pw")
    args = _make_import_args(v_path, str(tmp_path / "nonexistent.env"))
    with pytest.raises(SystemExit):
        cmd_import_env(args)


def test_import_no_overwrite_preserves_existing(tmp_path, env_file, capsys):
    v_path = str(tmp_path / "v.db")
    v = Vault(v_path, password="pw")
    v.set("FOO", "original")
    args = _make_import_args(v_path, env_file, no_overwrite=True)
    cmd_import_env(args)
    assert v.get("FOO") == "original"
    assert v.get("HELLO") == "world"


# --- export ---

def test_export_creates_env_file(tmp_path, src_vault):
    vault, v_path = src_vault
    out = str(tmp_path / "out.env")
    args = _make_export_args(v_path, out)
    cmd_export_env(args)
    assert Path(out).exists()


def test_export_prints_count(tmp_path, src_vault, capsys):
    vault, v_path = src_vault
    out = str(tmp_path / "out.env")
    args = _make_export_args(v_path, out)
    cmd_export_env(args)
    captured = capsys.readouterr().out
    assert "2 secret(s)" in captured


def test_export_subset_keys(tmp_path, src_vault, capsys):
    vault, v_path = src_vault
    out = str(tmp_path / "out.env")
    args = _make_export_args(v_path, out, keys=["FOO"])
    cmd_export_env(args)
    content = Path(out).read_text()
    assert "FOO" in content
    assert "HELLO" not in content


def test_export_empty_vault_exits(tmp_path):
    v_path = str(tmp_path / "empty.db")
    Vault(v_path, password="pw")  # empty vault
    out = str(tmp_path / "out.env")
    args = _make_export_args(v_path, out)
    with pytest.raises(SystemExit):
        cmd_export_env(args)
