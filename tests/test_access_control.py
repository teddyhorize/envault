"""Tests for envault.access_control."""
import pytest
from envault.access_control import (
    AccessControlError,
    grant_access,
    revoke_access,
    get_roles,
    list_access,
    has_role,
)


@pytest.fixture
def vault(tmp_path):
    vault_file = tmp_path / "test.vault"
    vault_file.write_text("{}")
    return str(vault_file)


def test_grant_access_adds_role(vault):
    grant_access(vault, "alice", "reader")
    assert "reader" in get_roles(vault, "alice")


def test_grant_access_multiple_roles(vault):
    grant_access(vault, "bob", "reader")
    grant_access(vault, "bob", "writer")
    roles = get_roles(vault, "bob")
    assert "reader" in roles
    assert "writer" in roles


def test_grant_duplicate_role_is_idempotent(vault):
    grant_access(vault, "alice", "reader")
    grant_access(vault, "alice", "reader")
    assert get_roles(vault, "alice").count("reader") == 1


def test_grant_invalid_role_raises(vault):
    with pytest.raises(AccessControlError, match="Invalid role"):
        grant_access(vault, "alice", "superuser")


def test_grant_empty_user_raises(vault):
    with pytest.raises(AccessControlError, match="empty"):
        grant_access(vault, "", "reader")


def test_revoke_specific_role(vault):
    grant_access(vault, "alice", "reader")
    grant_access(vault, "alice", "writer")
    revoke_access(vault, "alice", "reader")
    assert "reader" not in get_roles(vault, "alice")
    assert "writer" in get_roles(vault, "alice")


def test_revoke_all_roles(vault):
    grant_access(vault, "alice", "reader")
    grant_access(vault, "alice", "writer")
    revoke_access(vault, "alice")
    assert get_roles(vault, "alice") == []


def test_revoke_nonexistent_user_raises(vault):
    with pytest.raises(AccessControlError, match="no access entries"):
        revoke_access(vault, "ghost")


def test_revoke_role_not_held_raises(vault):
    grant_access(vault, "alice", "reader")
    with pytest.raises(AccessControlError, match="does not have role"):
        revoke_access(vault, "alice", "admin")


def test_has_role_true(vault):
    grant_access(vault, "alice", "admin")
    assert has_role(vault, "alice", "admin") is True


def test_has_role_false(vault):
    grant_access(vault, "alice", "reader")
    assert has_role(vault, "alice", "admin") is False


def test_list_access_returns_all_users(vault):
    grant_access(vault, "alice", "reader")
    grant_access(vault, "bob", "writer")
    acl = list_access(vault)
    assert "alice" in acl
    assert "bob" in acl


def test_get_roles_unknown_user_returns_empty(vault):
    assert get_roles(vault, "nobody") == []
