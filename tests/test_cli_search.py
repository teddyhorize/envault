"""Tests for envault.cli_search module."""

import argparse
import pytest

from envault.vault import Vault
from envault.tags import add_tag
from envault.cli_search import cmd_search_pattern, cmd_search_tag


PASSWORD = "cli-search-pw"


@pytest.fixture()
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "vault.json"), PASSWORD)
    v.set("DB_HOST", "localhost", PASSWORD)
    v.set("DB_PORT", "5432", PASSWORD)
    v.set("API_KEY", "mykey", PASSWORD)
    add_tag(v, "DB_HOST", "database")
    add_tag(v, "DB_PORT", "database")
    return v


def _make_args(vault_path, password, **kwargs):
    ns = argparse.Namespace(vault=vault_path, password=password, **kwargs)
    return ns


def test_search_pattern_prints_matches(src_vault, capsys):
    args = _make_args(src_vault.path, PASSWORD, pattern="DB_*")
    cmd_search_pattern(args)
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "DB_PORT" in out
    assert "API_KEY" not in out


def test_search_pattern_no_match_prints_message(src_vault, capsys):
    args = _make_args(src_vault.path, PASSWORD, pattern="MISSING_*")
    cmd_search_pattern(args)
    out = capsys.readouterr().out
    assert "No matching" in out


def test_search_pattern_empty_exits(src_vault):
    args = _make_args(src_vault.path, PASSWORD, pattern="")
    with pytest.raises(SystemExit):
        cmd_search_pattern(args)


def test_search_tag_prints_tagged_keys(src_vault, capsys):
    args = _make_args(src_vault.path, PASSWORD, tag="database")
    cmd_search_tag(args)
    out = capsys.readouterr().out
    assert "DB_HOST" in out
    assert "DB_PORT" in out
    assert "API_KEY" not in out


def test_search_tag_no_match_prints_message(src_vault, capsys):
    args = _make_args(src_vault.path, PASSWORD, tag="ghost")
    cmd_search_tag(args)
    out = capsys.readouterr().out
    assert "No matching" in out


def test_search_tag_empty_exits(src_vault):
    args = _make_args(src_vault.path, PASSWORD, tag="")
    with pytest.raises(SystemExit):
        cmd_search_tag(args)
