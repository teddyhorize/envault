"""Tests for envault/templates.py"""

import pytest

from envault.vault import Vault
from envault.templates import (
    TemplateError,
    define_template,
    delete_template,
    list_templates,
    validate_against_template,
    apply_template,
)

PASSWORD = "test-password"


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.json"))
    v.set("DB_HOST", "localhost", PASSWORD)
    v.set("DB_PORT", "5432", PASSWORD)
    return v


def test_define_template_and_list(vault):
    define_template(vault, "database", ["DB_HOST", "DB_PORT", "DB_NAME"])
    templates = list_templates(vault)
    assert "database" in templates
    assert templates["database"] == ["DB_HOST", "DB_PORT", "DB_NAME"]


def test_define_multiple_templates(vault):
    define_template(vault, "db", ["DB_HOST", "DB_PORT"])
    define_template(vault, "cache", ["REDIS_HOST", "REDIS_PORT"])
    templates = list_templates(vault)
    assert "db" in templates
    assert "cache" in templates


def test_define_template_empty_name_raises(vault):
    with pytest.raises(TemplateError, match="empty"):
        define_template(vault, "", ["KEY"])


def test_define_template_empty_keys_raises(vault):
    with pytest.raises(TemplateError, match="at least one key"):
        define_template(vault, "empty", [])


def test_delete_template(vault):
    define_template(vault, "db", ["DB_HOST"])
    delete_template(vault, "db")
    assert "db" not in list_templates(vault)


def test_delete_missing_template_raises(vault):
    with pytest.raises(TemplateError, match="not found"):
        delete_template(vault, "nonexistent")


def test_validate_all_present(vault):
    define_template(vault, "partial", ["DB_HOST", "DB_PORT"])
    missing = validate_against_template(vault, "partial", PASSWORD)
    assert missing == []


def test_validate_detects_missing_keys(vault):
    define_template(vault, "full", ["DB_HOST", "DB_PORT", "DB_NAME"])
    missing = validate_against_template(vault, "full", PASSWORD)
    assert "DB_NAME" in missing
    assert "DB_HOST" not in missing


def test_validate_unknown_template_raises(vault):
    with pytest.raises(TemplateError, match="not found"):
        validate_against_template(vault, "ghost", PASSWORD)


def test_apply_template_writes_all_keys(vault):
    define_template(vault, "app", ["APP_SECRET", "APP_ENV"])
    written = apply_template(
        vault, "app", {"APP_SECRET": "supersecret", "APP_ENV": "production"}, PASSWORD
    )
    assert written == 2
    assert vault.get("APP_SECRET", PASSWORD) == "supersecret"
    assert vault.get("APP_ENV", PASSWORD) == "production"


def test_apply_template_missing_value_raises(vault):
    define_template(vault, "incomplete", ["KEY_A", "KEY_B"])
    with pytest.raises(TemplateError, match="KEY_B"):
        apply_template(vault, "incomplete", {"KEY_A": "val"}, PASSWORD)


def test_apply_template_unknown_template_raises(vault):
    with pytest.raises(TemplateError, match="not found"):
        apply_template(vault, "ghost", {}, PASSWORD)


def test_list_templates_empty_when_none_defined(vault):
    assert list_templates(vault) == {}
