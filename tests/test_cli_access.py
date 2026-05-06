"""Tests for envault.cli_access."""
import argparse
import pytest
from envault.access_control import grant_access
from envault.cli_access import (
    cmd_grant,
    cmd_revoke,
    cmd_list_access,
    cmd_show_roles,
)


@pytest.fixture
def src_vault(tmp_path):
    vault_file = tmp_path / "test.vault"
    vault_file.write_text("{}")
    return str(vault_file)


def _make_args(**kwargs) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_grant_prints_confirmation(src_vault, capsys):
    args = _make_args(vault=src_vault, user="alice", role="reader")
    cmd_grant(args)
    out = capsys.readouterr().out
    assert "alice" in out
    assert "reader" in out


def test_grant_invalid_role_exits(src_vault, capsys):
    args = _make_args(vault=src_vault, user="alice", role="overlord")
    with pytest.raises(SystemExit) as exc:
        cmd_grant(args)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "Invalid role" in err


def test_grant_empty_user_exits(src_vault, capsys):
    args = _make_args(vault=src_vault, user="", role="reader")
    with pytest.raises(SystemExit) as exc:
        cmd_grant(args)
    assert exc.value.code == 1


def test_revoke_specific_role_prints_confirmation(src_vault, capsys):
    grant_access(src_vault, "bob", "writer")
    args = _make_args(vault=src_vault, user="bob", role="writer")
    cmd_revoke(args)
    out = capsys.readouterr().out
    assert "bob" in out
    assert "writer" in out


def test_revoke_all_roles_prints_confirmation(src_vault, capsys):
    grant_access(src_vault, "carol", "reader")
    args = _make_args(vault=src_vault, user="carol", role=None)
    cmd_revoke(args)
    out = capsys.readouterr().out
    assert "carol" in out
    assert "all" in out.lower()


def test_revoke_nonexistent_user_exits(src_vault, capsys):
    args = _make_args(vault=src_vault, user="ghost", role=None)
    with pytest.raises(SystemExit) as exc:
        cmd_revoke(args)
    assert exc.value.code == 1


def test_list_access_shows_users(src_vault, capsys):
    grant_access(src_vault, "alice", "reader")
    grant_access(src_vault, "bob", "admin")
    args = _make_args(vault=src_vault)
    cmd_list_access(args)
    out = capsys.readouterr().out
    assert "alice" in out
    assert "bob" in out


def test_list_access_empty_vault_prints_message(src_vault, capsys):
    args = _make_args(vault=src_vault)
    cmd_list_access(args)
    out = capsys.readouterr().out
    assert "No access entries" in out


def test_show_roles_for_user(src_vault, capsys):
    grant_access(src_vault, "dave", "writer")
    args = _make_args(vault=src_vault, user="dave")
    cmd_show_roles(args)
    out = capsys.readouterr().out
    assert "dave" in out
    assert "writer" in out


def test_show_roles_unknown_user_prints_message(src_vault, capsys):
    args = _make_args(vault=src_vault, user="nobody")
    cmd_show_roles(args)
    out = capsys.readouterr().out
    assert "no roles" in out.lower()
