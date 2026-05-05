"""Tests for envault.rotation module."""

import pytest
from unittest.mock import MagicMock
from envault.vault import Vault
from envault.rotation import RotationError, rotate_secret, rotate_all


@pytest.fixture
def vault(tmp_path):
    path = tmp_path / "test.vault"
    v = Vault(str(path), password="testpass")
    v.set("DB_PASSWORD", "old_db_pass")
    v.set("API_KEY", "old_api_key")
    return v


def test_rotate_secret_returns_old_value(vault):
    old = rotate_secret(vault, "DB_PASSWORD", "new_db_pass")
    assert old == "old_db_pass"


def test_rotate_secret_updates_vault(vault):
    rotate_secret(vault, "DB_PASSWORD", "new_db_pass")
    assert vault.get("DB_PASSWORD") == "new_db_pass"


def test_rotate_secret_missing_key_raises(vault):
    with pytest.raises(RotationError, match="not found"):
        rotate_secret(vault, "NONEXISTENT", "value")


def test_rotate_secret_empty_key_raises(vault):
    with pytest.raises(RotationError, match="Key must not be empty"):
        rotate_secret(vault, "", "value")


def test_rotate_secret_empty_value_raises(vault):
    with pytest.raises(RotationError, match="New value must not be empty"):
        rotate_secret(vault, "DB_PASSWORD", "")


def test_rotate_secret_records_audit(vault):
    mock_log = MagicMock()
    rotate_secret(vault, "DB_PASSWORD", "new_db_pass", audit_log=mock_log)
    mock_log.record.assert_called_once()
    call_kwargs = mock_log.record.call_args[1]
    assert call_kwargs["action"] == "rotate"
    assert call_kwargs["key"] == "DB_PASSWORD"


def test_rotate_secret_no_audit_when_none(vault):
    # Should not raise even without an audit log
    old = rotate_secret(vault, "API_KEY", "new_api_key", audit_log=None)
    assert old == "old_api_key"


def test_rotate_all_returns_previous_values(vault):
    previous = rotate_all(vault, {"DB_PASSWORD": "new_db", "API_KEY": "new_api"})
    assert previous["DB_PASSWORD"] == "old_db_pass"
    assert previous["API_KEY"] == "old_api_key"


def test_rotate_all_updates_all_keys(vault):
    rotate_all(vault, {"DB_PASSWORD": "new_db", "API_KEY": "new_api"})
    assert vault.get("DB_PASSWORD") == "new_db"
    assert vault.get("API_KEY") == "new_api"


def test_rotate_all_empty_mapping_raises(vault):
    with pytest.raises(RotationError, match="must not be empty"):
        rotate_all(vault, {})


def test_rotate_all_missing_key_raises(vault):
    with pytest.raises(RotationError, match="not found"):
        rotate_all(vault, {"DB_PASSWORD": "new_db", "GHOST_KEY": "value"})
