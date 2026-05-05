"""Tests for envault.diff module."""

import pytest
from envault.vault import Vault
from envault.diff import DiffResult, DiffError, diff_vaults


PASSWORD = "test-pass"


@pytest.fixture
def left_vault(tmp_path):
    v = Vault(str(tmp_path / "left.vault"), PASSWORD)
    v.set("KEY_A", "value_a", PASSWORD)
    v.set("KEY_B", "value_b", PASSWORD)
    v.set("KEY_COMMON", "same", PASSWORD)
    return v


@pytest.fixture
def right_vault(tmp_path):
    v = Vault(str(tmp_path / "right.vault"), PASSWORD)
    v.set("KEY_B", "value_b_changed", PASSWORD)
    v.set("KEY_C", "value_c", PASSWORD)
    v.set("KEY_COMMON", "same", PASSWORD)
    return v


def test_diff_detects_added_keys(left_vault, right_vault):
    result = diff_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    assert "KEY_C" in result.added


def test_diff_detects_removed_keys(left_vault, right_vault):
    result = diff_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    assert "KEY_A" in result.removed


def test_diff_detects_changed_keys(left_vault, right_vault):
    result = diff_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    assert "KEY_B" in result.changed


def test_diff_detects_unchanged_keys(left_vault, right_vault):
    result = diff_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    assert "KEY_COMMON" in result.unchanged


def test_has_differences_true(left_vault, right_vault):
    result = diff_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    assert result.has_differences is True


def test_has_differences_false(tmp_path):
    v1 = Vault(str(tmp_path / "a.vault"), PASSWORD)
    v2 = Vault(str(tmp_path / "b.vault"), PASSWORD)
    v1.set("X", "1", PASSWORD)
    v2.set("X", "1", PASSWORD)
    result = diff_vaults(v1, PASSWORD, v2, PASSWORD)
    assert result.has_differences is False


def test_summary_contains_symbols(left_vault, right_vault):
    result = diff_vaults(left_vault, PASSWORD, right_vault, PASSWORD)
    summary = result.summary()
    assert "+" in summary
    assert "-" in summary
    assert "~" in summary


def test_empty_vaults_no_differences(tmp_path):
    v1 = Vault(str(tmp_path / "e1.vault"), PASSWORD)
    v2 = Vault(str(tmp_path / "e2.vault"), PASSWORD)
    result = diff_vaults(v1, PASSWORD, v2, PASSWORD)
    assert not result.has_differences
    assert result.summary() == "(no secrets)"
