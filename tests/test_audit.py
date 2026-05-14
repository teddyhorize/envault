"""Tests for envault.audit module."""

import os
import pytest
from pathlib import Path

from envault.audit import AuditLog, AuditEntry


@pytest.fixture
def audit(tmp_path):
    vault_file = tmp_path / "test.vault"
    vault_file.touch()
    return AuditLog(str(vault_file))


def test_record_creates_entry(audit):
    audit.record("set", key="DB_PASSWORD", actor="alice")
    entries = audit.entries()
    assert len(entries) == 1
    assert entries[0].action == "set"
    assert entries[0].key == "DB_PASSWORD"
    assert entries[0].actor == "alice"


def test_record_multiple_entries(audit):
    audit.record("set", key="FOO", actor="alice")
    audit.record("get", key="FOO", actor="bob")
    audit.record("delete", key="FOO", actor="alice")
    entries = audit.entries()
    assert len(entries) == 3
    assert [e.action for e in entries] == ["set", "get", "delete"]


def test_entry_has_timestamp(audit):
    audit.record("set", key="API_KEY", actor="ci")
    entry = audit.entries()[0]
    assert entry.timestamp is not None
    assert "T" in entry.timestamp  # ISO format contains 'T'


def test_entries_empty_when_no_log(audit):
    assert audit.entries() == []


def test_clear_removes_all_entries(audit):
    audit.record("set", key="X", actor="alice")
    audit.record("set", key="Y", actor="alice")
    audit.clear()
    assert audit.entries() == []


def test_clear_is_idempotent(audit):
    audit.clear()  # no log file yet — should not raise
    assert audit.entries() == []


def test_actor_falls_back_to_env_user(audit, monkeypatch):
    monkeypatch.setenv("USER", "envuser")
    audit.record("set", key="TOKEN")
    assert audit.entries()[0].actor == "envuser"


def test_actor_falls_back_to_unknown(audit, monkeypatch):
    monkeypatch.delenv("USER", raising=False)
    audit.record("set", key="TOKEN")
    assert audit.entries()[0].actor == "unknown"


def test_entry_repr(audit):
    audit.record("set", key="K", actor="dev")
    entry = audit.entries()[0]
    assert "set" in repr(entry)
    assert "K" in repr(entry)


def test_audit_log_persists_across_instances(tmp_path):
    vault_file = tmp_path / "vault.env"
    vault_file.touch()
    log1 = AuditLog(str(vault_file))
    log1.record("set", key="PERSIST", actor="alice")

    log2 = AuditLog(str(vault_file))
    entries = log2.entries()
    assert len(entries) == 1
    assert entries[0].key == "PERSIST"


def test_entries_filter_by_action(audit):
    """Entries can be filtered by action type to narrow audit review."""
    audit.record("set", key="FOO", actor="alice")
    audit.record("get", key="FOO", actor="bob")
    audit.record("set", key="BAR", actor="alice")
    audit.record("delete", key="FOO", actor="alice")

    set_entries = [e for e in audit.entries() if e.action == "set"]
    assert len(set_entries) == 2
    assert all(e.action == "set" for e in set_entries)

    get_entries = [e for e in audit.entries() if e.action == "get"]
    assert len(get_entries) == 1
    assert get_entries[0].actor == "bob"
