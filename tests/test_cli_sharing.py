"""Tests for envault.cli_sharing — export-bundle / import-bundle commands."""

import pytest
from pathlib import Path
from unittest.mock import patch

from envault.vault import Vault
from envault.cli_sharing import cmd_export_bundle, cmd_import_bundle


VAULT_PASS = "vpass"
SHARE_PASS = "spass"


@pytest.fixture
def src_vault(tmp_path):
    v = Vault(tmp_path / "src.json")
    v.set("TOKEN", "secret-token", VAULT_PASS)
    v.set("HOST", "example.com", VAULT_PASS)
    return v, str(tmp_path / "src.json")


@pytest.fixture
def dst_vault_path(tmp_path):
    return str(tmp_path / "dst.json")


def test_export_prints_bundle_to_stdout(src_vault, capsys):
    _, path = src_vault
    cmd_export_bundle(path, VAULT_PASS, SHARE_PASS)
    captured = capsys.readouterr()
    assert len(captured.out.strip()) > 0


def test_export_writes_bundle_to_file(src_vault, tmp_path):
    _, path = src_vault
    out_file = str(tmp_path / "bundle.txt")
    cmd_export_bundle(path, VAULT_PASS, SHARE_PASS, output_file=out_file)
    assert Path(out_file).exists()
    assert len(Path(out_file).read_text().strip()) > 0


def test_export_wrong_vault_password_exits(src_vault, capsys):
    _, path = src_vault
    with pytest.raises(SystemExit) as exc_info:
        cmd_export_bundle(path, "wrong", SHARE_PASS)
    assert exc_info.value.code == 1


def test_import_from_file(src_vault, dst_vault_path, tmp_path):
    _, path = src_vault
    bundle_file = str(tmp_path / "bundle.txt")
    cmd_export_bundle(path, VAULT_PASS, SHARE_PASS, output_file=bundle_file)

    cmd_import_bundle(dst_vault_path, VAULT_PASS, SHARE_PASS, bundle_file)

    dst = Vault(Path(dst_vault_path))
    assert dst.get("TOKEN", VAULT_PASS) == "secret-token"
    assert dst.get("HOST", VAULT_PASS) == "example.com"


def test_import_from_inline_string(src_vault, dst_vault_path, capsys):
    _, path = src_vault
    cmd_export_bundle(path, VAULT_PASS, SHARE_PASS)
    bundle_str = capsys.readouterr().out.strip()

    cmd_import_bundle(dst_vault_path, VAULT_PASS, SHARE_PASS, bundle_str)
    dst = Vault(Path(dst_vault_path))
    assert dst.get("TOKEN", VAULT_PASS) == "secret-token"


def test_import_wrong_share_password_exits(src_vault, dst_vault_path, capsys):
    _, path = src_vault
    cmd_export_bundle(path, VAULT_PASS, SHARE_PASS)
    bundle_str = capsys.readouterr().out.strip()

    with pytest.raises(SystemExit) as exc_info:
        cmd_import_bundle(dst_vault_path, VAULT_PASS, "wrong-share", bundle_str)
    assert exc_info.value.code == 1


def test_import_prints_imported_keys(src_vault, dst_vault_path, capsys):
    _, path = src_vault
    cmd_export_bundle(path, VAULT_PASS, SHARE_PASS)
    bundle_str = capsys.readouterr().out.strip()

    cmd_import_bundle(dst_vault_path, VAULT_PASS, SHARE_PASS, bundle_str)
    captured = capsys.readouterr()
    assert "Imported 2 secret(s)" in captured.out
