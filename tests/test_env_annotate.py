"""Tests for envault.env_annotate."""

import pytest
from pathlib import Path
from envault.vault import Vault
from envault.env_annotate import (
    AnnotateError,
    set_annotation,
    get_annotation,
    remove_annotation,
    list_annotations,
)


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="testpass")
    v.set("DB_HOST", "localhost")
    v.set("DB_PORT", "5432")
    v.set("API_KEY", "secret-key")
    return v


def test_set_and_get_annotation(vault):
    set_annotation(vault, "DB_HOST", "Database hostname")
    assert get_annotation(vault, "DB_HOST") == "Database hostname"


def test_get_annotation_not_set_returns_none(vault):
    assert get_annotation(vault, "DB_PORT") is None


def test_set_annotation_missing_key_raises(vault):
    with pytest.raises(AnnotateError, match="does not exist"):
        set_annotation(vault, "NONEXISTENT", "some description")


def test_set_annotation_empty_key_raises(vault):
    with pytest.raises(AnnotateError, match="empty"):
        set_annotation(vault, "", "description")


def test_get_annotation_empty_key_raises(vault):
    with pytest.raises(AnnotateError, match="empty"):
        get_annotation(vault, "")


def test_remove_annotation_returns_true_when_exists(vault):
    set_annotation(vault, "API_KEY", "The API key")
    result = remove_annotation(vault, "API_KEY")
    assert result is True
    assert get_annotation(vault, "API_KEY") is None


def test_remove_annotation_returns_false_when_not_set(vault):
    result = remove_annotation(vault, "DB_HOST")
    assert result is False


def test_remove_annotation_empty_key_raises(vault):
    with pytest.raises(AnnotateError, match="empty"):
        remove_annotation(vault, "")


def test_list_annotations_empty_when_none_set(vault):
    assert list_annotations(vault) == {}


def test_list_annotations_returns_all(vault):
    set_annotation(vault, "DB_HOST", "Hostname")
    set_annotation(vault, "API_KEY", "Key for external API")
    result = list_annotations(vault)
    assert result == {"DB_HOST": "Hostname", "API_KEY": "Key for external API"}


def test_set_annotation_overwrites_existing(vault):
    set_annotation(vault, "DB_HOST", "Old description")
    set_annotation(vault, "DB_HOST", "New description")
    assert get_annotation(vault, "DB_HOST") == "New description"


def test_annotations_persist_across_calls(vault):
    set_annotation(vault, "DB_PORT", "Port number")
    # Simulate a fresh load by calling list_annotations again
    all_ann = list_annotations(vault)
    assert "DB_PORT" in all_ann
    assert all_ann["DB_PORT"] == "Port number"
