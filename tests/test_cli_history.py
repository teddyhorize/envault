"""Tests for envault.cli_history module."""
import argparse
import pytest

from envault.vault import Vault
from envault.history import record_version
from envault.cli_history import (
    cmd_history_show,
    cmd_history_latest,
    cmd_history_clear,
)


@pytest.fixture
def src_vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="pw")
    v.set("TOKEN", "abc")
    record_version(v, "TOKEN", "v1")
    record_version(v, "TOKEN", "v2")
    return v


def _make_args(vault, key="TOKEN", password="pw", **kwargs):
    ns = argparse.Namespace(vault=vault.path, password=password, key=key, **kwargs)
    return ns


def test_show_prints_all_versions(src_vault, capsys):
    cmd_history_show(_make_args(src_vault))
    out = capsys.readouterr().out
    assert "v1" in out
    assert "v2" in out
    assert "2 version" in out


def test_show_no_history_prints_message(src_vault, capsys):
    cmd_history_show(_make_args(src_vault, key="MISSING"))
    out = capsys.readouterr().out
    assert "No history" in out


def test_latest_prints_most_recent(src_vault, capsys):
    cmd_history_latest(_make_args(src_vault))
    out = capsys.readouterr().out
    assert "v2" in out
    assert "latest" in out


def test_latest_no_history_prints_message(src_vault, capsys):
    cmd_history_latest(_make_args(src_vault, key="NOPE"))
    out = capsys.readouterr().out
    assert "No history" in out


def test_clear_removes_history(src_vault, capsys):
    cmd_history_clear(_make_args(src_vault))
    out = capsys.readouterr().out
    assert "Cleared 2" in out


def test_clear_empty_history_reports_zero(src_vault, capsys):
    cmd_history_clear(_make_args(src_vault, key="TOKEN"))
    cmd_history_clear(_make_args(src_vault, key="TOKEN"))
    out = capsys.readouterr().out
    assert "Cleared 0" in out


def test_show_wrong_password_exits(src_vault):
    args = _make_args(src_vault, password="wrong")
    with pytest.raises(SystemExit):
        cmd_history_show(args)
