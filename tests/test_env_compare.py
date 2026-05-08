"""Tests for envault.env_compare."""

import pytest

from envault.vault import Vault
from envault.env_compare import (
    CompareError,
    CompareResult,
    compare_vaults,
    _preview,
)

PASSWORD = "test-pass"


@pytest.fixture
def left_vault(tmp_path):
    v = Vault(str(tmp_path / "left.vault"))
    v.set("DB_HOST", "localhost", PASSWORD)
    v.set("DB_PORT", "5432", PASSWORD)
    v.set("API_KEY", "secret123", PASSWORD)
    return v


@pytest.fixture
def right_vault(tmp_path):
    v = Vault(str(tmp_path / "right.vault"))
    v.set("DB_HOST", "prod.db.example.com", PASSWORD)
    v.set("DB_PORT", "5432", PASSWORD)
    v.set("NEW_KEY", "newvalue", PASSWORD)
    return v


@pytest.fixture
def identical_vault(tmp_path, left_vault):
    v = Vault(str(tmp_path / "identical.vault"))
    for key in left_vault.list_keys():
        v.set(key, left_vault.get(key, PASSWORD), PASSWORD)
    return v


def test_compare_detects_only_in_left(left_vault, right_vault):
    result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    assert "API_KEY" in result.only_in_left


def test_compare_detects_only_in_right(left_vault, right_vault):
    result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    assert "NEW_KEY" in result.only_in_right


def test_compare_detects_changed_keys(left_vault, right_vault):
    result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    assert "DB_HOST" in result.changed


def test_compare_detects_identical_keys(left_vault, right_vault):
    result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    assert "DB_PORT" in result.identical


def test_has_differences_true(left_vault, right_vault):
    result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    assert result.has_differences is True


def test_has_differences_false(left_vault, identical_vault):
    result = compare_vaults(left_vault, PASSWORD, identical_vault, PASSWORD)
    assert result.has_differences is False


def test_summary_identical(left_vault, identical_vault):
    result = compare_vaults(left_vault, PASSWORD, identical_vault, PASSWORD)
    assert result.summary() == "Vaults are identical."


def test_summary_contains_diff_markers(left_vault, right_vault):
    result = compare_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    summary = result.summary()
    assert "<" in summary or ">" in summary or "~" in summary


def test_preview_masks_short_value():
    assert _preview("abc") == "***"


def test_preview_masks_long_value():
    preview = _preview("supersecretvalue")
    assert "***" in preview
    assert "supersecretvalue" not in preview
