"""Tests for envault.env_validate."""

import pytest

from envault.vault import Vault
from envault.env_validate import (
    ValidationError,
    ValidationIssue,
    ValidationResult,
    validate_vault,
)

PASSWORD = "test-password"


@pytest.fixture()
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.db"), PASSWORD)
    v.set("DATABASE_URL", "postgres://localhost/mydb", PASSWORD)
    v.set("API_KEY", "abc123", PASSWORD)
    v.set("PORT", "8080", PASSWORD)
    return v


@pytest.fixture()
def empty_vault(tmp_path):
    return Vault(str(tmp_path / "empty.db"), PASSWORD)


# --- ValidationResult helpers ---

def test_result_no_issues_has_no_issues():
    r = ValidationResult()
    assert not r.has_issues


def test_result_with_issues_has_issues():
    r = ValidationResult(issues=[ValidationIssue("K", "required", "missing")])
    assert r.has_issues


def test_summary_clean():
    assert "passed" in ValidationResult().summary()


def test_summary_with_issues():
    r = ValidationResult(issues=[ValidationIssue("FOO", "required", "Key is missing from vault.")])
    summary = r.summary()
    assert "1 validation issue" in summary
    assert "FOO" in summary


# --- validate_vault ---

def test_no_rules_returns_clean(vault):
    result = validate_vault(vault, PASSWORD)
    assert not result.has_issues


def test_required_key_present_no_issue(vault):
    result = validate_vault(vault, PASSWORD, required_keys=["DATABASE_URL"])
    assert not result.has_issues


def test_required_key_missing_raises_issue(vault):
    result = validate_vault(vault, PASSWORD, required_keys=["MISSING_KEY"])
    assert result.has_issues
    assert any(i.key == "MISSING_KEY" and i.rule == "required" for i in result.issues)


def test_multiple_required_keys_all_missing(vault):
    result = validate_vault(vault, PASSWORD, required_keys=["X", "Y"])
    missing = {i.key for i in result.issues if i.rule == "required"}
    assert missing == {"X", "Y"}


def test_pattern_match_passes(vault):
    result = validate_vault(vault, PASSWORD, patterns={"PORT": r"\d+"})
    assert not result.has_issues


def test_pattern_mismatch_reports_issue(vault):
    result = validate_vault(vault, PASSWORD, patterns={"API_KEY": r"\d{10,}"})
    assert result.has_issues
    assert any(i.key == "API_KEY" and i.rule == "pattern" for i in result.issues)


def test_non_empty_flag_detects_empty_value(tmp_path):
    v = Vault(str(tmp_path / "v.db"), PASSWORD)
    v.set("EMPTY_KEY", "", PASSWORD)
    result = validate_vault(v, PASSWORD, non_empty=True)
    assert any(i.key == "EMPTY_KEY" and i.rule == "non_empty" for i in result.issues)


def test_non_empty_false_ignores_empty_value(tmp_path):
    v = Vault(str(tmp_path / "v.db"), PASSWORD)
    v.set("EMPTY_KEY", "", PASSWORD)
    result = validate_vault(v, PASSWORD, non_empty=False)
    assert not result.has_issues


def test_invalid_regex_raises_validation_error(vault):
    with pytest.raises(ValidationError, match="Invalid regex"):
        validate_vault(vault, PASSWORD, patterns={"PORT": "[invalid"})


def test_empty_vault_no_issues(empty_vault):
    result = validate_vault(empty_vault, PASSWORD, required_keys=[], patterns={})
    assert not result.has_issues
