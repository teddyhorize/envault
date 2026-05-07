"""Tests for envault.env_merge module."""
from __future__ import annotations

import pytest

from envault.vault import Vault
from envault.env_merge import (
    ConflictStrategy,
    MergeError,
    MergeResult,
    merge_vaults,
)


@pytest.fixture
def left_vault(tmp_path):
    v = Vault(str(tmp_path / "left.vault"), password="leftpass")
    v.set("SHARED_KEY", "left_value")
    v.set("LEFT_ONLY", "only_in_left")
    return v


@pytest.fixture
def right_vault(tmp_path):
    v = Vault(str(tmp_path / "right.vault"), password="rightpass")
    v.set("SHARED_KEY", "right_value")
    v.set("RIGHT_ONLY", "only_in_right")
    return v


@pytest.fixture
def empty_vault(tmp_path):
    return Vault(str(tmp_path / "empty.vault"), password="emptypass")


def test_merge_adds_new_keys(right_vault, left_vault):
    result = merge_vaults(right_vault, left_vault, strategy=ConflictStrategy.KEEP_RIGHT)
    assert "RIGHT_ONLY" in result.added
    assert left_vault.get("RIGHT_ONLY") == "only_in_right"


def test_merge_keep_right_overwrites_conflict(left_vault, right_vault):
    result = merge_vaults(left_vault, right_vault, strategy=ConflictStrategy.KEEP_RIGHT)
    assert "SHARED_KEY" in result.updated
    assert right_vault.get("SHARED_KEY") == "left_value"


def test_merge_keep_left_preserves_destination(left_vault, right_vault):
    result = merge_vaults(left_vault, right_vault, strategy=ConflictStrategy.KEEP_LEFT)
    assert "SHARED_KEY" in result.skipped
    assert right_vault.get("SHARED_KEY") == "right_value"


def test_merge_fail_strategy_raises_on_conflict(left_vault, right_vault):
    with pytest.raises(MergeError, match="Conflict on key 'SHARED_KEY'"):
        merge_vaults(left_vault, right_vault, strategy=ConflictStrategy.FAIL)


def test_merge_into_empty_vault_all_added(left_vault, empty_vault):
    result = merge_vaults(left_vault, empty_vault)
    assert set(result.added) == {"SHARED_KEY", "LEFT_ONLY"}
    assert result.updated == []
    assert result.conflicts == []


def test_merge_selective_keys(left_vault, empty_vault):
    result = merge_vaults(left_vault, empty_vault, keys=["LEFT_ONLY"])
    assert result.added == ["LEFT_ONLY"]
    assert empty_vault.get("SHARED_KEY") is None


def test_merge_skips_missing_source_keys(left_vault, empty_vault):
    result = merge_vaults(left_vault, empty_vault, keys=["NONEXISTENT"])
    assert "NONEXISTENT" in result.skipped
    assert result.added == []


def test_merge_result_has_no_conflicts_flag(left_vault, empty_vault):
    result = merge_vaults(left_vault, empty_vault)
    assert not result.has_conflicts


def test_merge_result_has_conflicts_flag(left_vault, right_vault):
    result = merge_vaults(left_vault, right_vault, strategy=ConflictStrategy.KEEP_RIGHT)
    assert result.has_conflicts


def test_merge_result_summary_contains_counts(left_vault, empty_vault):
    result = merge_vaults(left_vault, empty_vault)
    summary = result.summary()
    assert "Added" in summary
    assert "Updated" in summary
    assert "Skipped" in summary
