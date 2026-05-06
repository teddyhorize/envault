"""Tests for envault.import_export_env."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

from envault.vault import Vault
from envault.import_export_env import (
    EnvFileError,
    export_to_env_file,
    import_from_env_file,
    parse_env_file,
)


@pytest.fixture()
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.db"), password="secret")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "abc123")
    return v


@pytest.fixture()
def env_file(tmp_path):
    p = tmp_path / ".env"
    p.write_text("DB_HOST=localhost\nDB_PORT=5432\nAPI_KEY=abc123\n", encoding="utf-8")
    return str(p)


# --- parse_env_file ---

def test_parse_basic_env_file(env_file):
    result = parse_env_file(env_file)
    assert result == {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "abc123"}


def test_parse_env_file_with_export_prefix(tmp_path):
    p = tmp_path / ".env"
    p.write_text("export FOO=bar\nexport BAZ=qux\n", encoding="utf-8")
    assert parse_env_file(str(p)) == {"FOO": "bar", "BAZ": "qux"}


def test_parse_env_file_strips_quotes(tmp_path):
    p = tmp_path / ".env"
    p.write_text('KEY1="hello world"\nKEY2=\'single\'\n', encoding="utf-8")
    result = parse_env_file(str(p))
    assert result["KEY1"] == "hello world"
    assert result["KEY2"] == "single"


def test_parse_env_file_ignores_comments(tmp_path):
    p = tmp_path / ".env"
    p.write_text("# comment\nKEY=val\n\n# another\n", encoding="utf-8")
    assert parse_env_file(str(p)) == {"KEY": "val"}


def test_parse_env_file_invalid_line_raises(tmp_path):
    p = tmp_path / ".env"
    p.write_text("THIS IS INVALID\n", encoding="utf-8")
    with pytest.raises(EnvFileError, match="Unparseable"):
        parse_env_file(str(p))


# --- import_from_env_file ---

def test_import_adds_secrets_to_vault(tmp_path, env_file):
    v = Vault(str(tmp_path / "v.db"), password="pw")
    imported = import_from_env_file(v, env_file)
    assert set(imported) == {"DB_HOST", "DB_PORT", "API_KEY"}
    assert v.get("DB_HOST") == "localhost"


def test_import_empty_file_raises(tmp_path):
    p = tmp_path / "empty.env"
    p.write_text("# only comments\n", encoding="utf-8")
    v = Vault(str(tmp_path / "v.db"), password="pw")
    with pytest.raises(EnvFileError):
        import_from_env_file(v, str(p))


def test_import_no_overwrite_skips_existing(tmp_path, env_file):
    v = Vault(str(tmp_path / "v.db"), password="pw")
    v.set("DB_HOST", "original")
    import_from_env_file(v, env_file, overwrite=False)
    assert v.get("DB_HOST") == "original"
    assert v.get("DB_PORT") == "5432"


# --- export_to_env_file ---

def test_export_creates_file(vault, tmp_path):
    out = str(tmp_path / "out.env")
    export_to_env_file(vault, out)
    assert Path(out).exists()


def test_export_contains_all_keys(vault, tmp_path):
    out = str(tmp_path / "out.env")
    export_to_env_file(vault, out)
    result = parse_env_file(out)
    assert result["DB_HOST"] == "localhost"
    assert result["API_KEY"] == "abc123"


def test_export_subset_of_keys(vault, tmp_path):
    out = str(tmp_path / "out.env")
    exported = export_to_env_file(vault, out, keys=["DB_HOST"])
    assert exported == ["DB_HOST"]
    result = parse_env_file(out)
    assert "DB_PORT" not in result


def test_export_empty_vault_raises(tmp_path):
    v = Vault(str(tmp_path / "v.db"), password="pw")
    with pytest.raises(EnvFileError):
        export_to_env_file(v, str(tmp_path / "out.env"))


def test_roundtrip_import_export(vault, tmp_path):
    out = str(tmp_path / "out.env")
    export_to_env_file(vault, out)
    v2 = Vault(str(tmp_path / "v2.db"), password="pw2")
    import_from_env_file(v2, out)
    assert v2.get("DB_HOST") == vault.get("DB_HOST")
    assert v2.get("API_KEY") == vault.get("API_KEY")
