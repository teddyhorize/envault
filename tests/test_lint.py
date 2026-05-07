"""Tests for envault.lint."""

import pytest

from envault.vault import Vault
from envault.lint import lint_vault, LintError, LintResult


PASSWORD = "test-password"


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.json"), PASSWORD)
    return v


def test_lint_empty_vault_warns(vault):
    result = lint_vault(vault, PASSWORD)
    assert result.has_issues
    assert any("empty" in i.message.lower() for i in result.warnings)


def test_lint_clean_vault_no_issues(vault):
    vault.set("API_KEY", "supersecretvalue123", PASSWORD)
    vault.set("DB_PASSWORD", "another_strong_secret", PASSWORD)
    result = lint_vault(vault, PASSWORD)
    assert not result.has_issues
    assert result.summary() == "No issues found."


def test_lint_detects_bad_key_naming(vault):
    vault.set("bad-key", "somevalue", PASSWORD)
    result = lint_vault(vault, PASSWORD)
    keys_flagged = [i.key for i in result.warnings]
    assert "bad-key" in keys_flagged


def test_lint_detects_lowercase_key(vault):
    vault.set("mykey", "somevalue", PASSWORD)
    result = lint_vault(vault, PASSWORD)
    keys_flagged = [i.key for i in result.warnings]
    assert "mykey" in keys_flagged


def test_lint_detects_empty_value(vault):
    vault.set("EMPTY_SECRET", "   ", PASSWORD)
    result = lint_vault(vault, PASSWORD)
    errors = [i for i in result.errors if i.key == "EMPTY_SECRET"]
    assert errors
    assert "empty" in errors[0].message.lower()


def test_lint_detects_placeholder_value(vault):
    vault.set("API_TOKEN", "CHANGE_ME", PASSWORD)
    result = lint_vault(vault, PASSWORD)
    errors = [i for i in result.errors if i.key == "API_TOKEN"]
    assert errors
    assert "placeholder" in errors[0].message.lower()


def test_lint_detects_short_value(vault):
    vault.set("SHORT_KEY", "abc", PASSWORD)
    result = lint_vault(vault, PASSWORD)
    warnings = [i for i in result.warnings if i.key == "SHORT_KEY"]
    assert warnings
    assert "short" in warnings[0].message.lower()


def test_lint_summary_counts(vault):
    vault.set("bad-key", "CHANGE_ME", PASSWORD)
    result = lint_vault(vault, PASSWORD)
    assert "error" in result.summary()
    assert "warning" in result.summary()


def test_lint_raises_on_invalid_input():
    with pytest.raises(LintError):
        lint_vault("not_a_vault", PASSWORD)


def test_lint_result_errors_and_warnings_split(vault):
    vault.set("bad-key", "CHANGE_ME", PASSWORD)
    result = lint_vault(vault, PASSWORD)
    for issue in result.errors:
        assert issue.severity == "error"
    for issue in result.warnings:
        assert issue.severity == "warning"
