"""Tests for envault.env_audit_export."""
from __future__ import annotations

import csv
import io
import json
import os
import tempfile

import pytest

from envault.vault import Vault
from envault.audit import AuditLog
from envault.env_audit_export import export_audit_log, AuditExportError


PASSWORD = "test-pass"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.db"), PASSWORD)
    v.set("API_KEY", "abc123")
    v.set("DB_PASS", "secret")
    log = AuditLog(str(tmp_path / "vault.db"), PASSWORD)
    log.record("set", "API_KEY")
    log.record("set", "DB_PASS")
    return str(tmp_path / "vault.db"), PASSWORD


def test_export_json_returns_string(vault):
    vault_path, password = vault
    result = export_audit_log(vault_path, password, fmt="json")
    assert isinstance(result, str)


def test_export_json_is_valid_json(vault):
    vault_path, password = vault
    result = export_audit_log(vault_path, password, fmt="json")
    parsed = json.loads(result)
    assert isinstance(parsed, list)


def test_export_json_contains_entries(vault):
    vault_path, password = vault
    result = export_audit_log(vault_path, password, fmt="json")
    parsed = json.loads(result)
    assert len(parsed) == 2


def test_export_json_entry_has_required_fields(vault):
    vault_path, password = vault
    result = export_audit_log(vault_path, password, fmt="json")
    parsed = json.loads(result)
    for entry in parsed:
        assert "action" in entry
        assert "key" in entry
        assert "timestamp" in entry


def test_export_csv_returns_string(vault):
    vault_path, password = vault
    result = export_audit_log(vault_path, password, fmt="csv")
    assert isinstance(result, str)


def test_export_csv_has_header(vault):
    vault_path, password = vault
    result = export_audit_log(vault_path, password, fmt="csv")
    reader = csv.DictReader(io.StringIO(result))
    assert "action" in reader.fieldnames
    assert "key" in reader.fieldnames
    assert "timestamp" in reader.fieldnames


def test_export_csv_row_count(vault):
    vault_path, password = vault
    result = export_audit_log(vault_path, password, fmt="csv")
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 2


def test_export_unsupported_format_raises(vault):
    vault_path, password = vault
    with pytest.raises(AuditExportError, match="Unsupported format"):
        export_audit_log(vault_path, password, fmt="xml")


def test_export_writes_to_file(vault, tmp_path):
    vault_path, password = vault
    out = str(tmp_path / "audit.json")
    export_audit_log(vault_path, password, fmt="json", output_path=out)
    assert os.path.exists(out)
    with open(out) as f:
        parsed = json.load(f)
    assert isinstance(parsed, list)
