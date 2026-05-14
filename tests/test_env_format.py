"""Tests for envault.env_format."""

from __future__ import annotations

import base64
import os
import tempfile

import pytest

from envault.vault import Vault
from envault.env_format import (
    FormatError,
    VALID_FORMATS,
    apply_format,
    format_secret,
    format_and_store,
)

PASSWORD = "testpass"


@pytest.fixture
def vault(tmp_path):
    path = str(tmp_path / "test.vault")
    v = Vault(path, PASSWORD)
    v.set("MY_KEY", "hello world")
    v.set("ENCODED", base64.b64encode(b"decoded").decode())
    return v


# --- apply_format ---

def test_apply_format_upper():
    assert apply_format("hello", "upper") == "HELLO"


def test_apply_format_lower():
    assert apply_format("HELLO", "lower") == "hello"


def test_apply_format_strip():
    assert apply_format("  spaces  ", "strip") == "spaces"


def test_apply_format_base64_encodes():
    result = apply_format("secret", "base64")
    assert result == base64.b64encode(b"secret").decode()


def test_apply_format_unbase64_decodes():
    encoded = base64.b64encode(b"decoded").decode()
    assert apply_format(encoded, "unbase64") == "decoded"


def test_apply_format_unknown_raises():
    with pytest.raises(FormatError, match="Unknown format"):
        apply_format("value", "nonexistent")


def test_apply_format_empty_fmt_raises():
    with pytest.raises(FormatError, match="must not be empty"):
        apply_format("value", "")


def test_valid_formats_list_is_populated():
    assert len(VALID_FORMATS) >= 5
    assert "upper" in VALID_FORMATS
    assert "base64" in VALID_FORMATS


# --- format_secret ---

def test_format_secret_returns_formatted_value(vault):
    result = format_secret(vault, "MY_KEY", "upper")
    assert result == "HELLO WORLD"


def test_format_secret_missing_key_raises(vault):
    with pytest.raises(FormatError, match="not found"):
        format_secret(vault, "MISSING", "upper")


def test_format_secret_empty_key_raises(vault):
    with pytest.raises(FormatError, match="must not be empty"):
        format_secret(vault, "", "upper")


def test_format_secret_does_not_modify_vault(vault):
    format_secret(vault, "MY_KEY", "upper")
    assert vault.get("MY_KEY") == "hello world"


# --- format_and_store ---

def test_format_and_store_overwrites_original(vault):
    result = format_and_store(vault, "MY_KEY", "upper")
    assert result == "HELLO WORLD"
    assert vault.get("MY_KEY") == "HELLO WORLD"


def test_format_and_store_writes_to_dest_key(vault):
    format_and_store(vault, "MY_KEY", "upper", dest_key="MY_KEY_UPPER")
    assert vault.get("MY_KEY") == "hello world"  # original unchanged
    assert vault.get("MY_KEY_UPPER") == "HELLO WORLD"


def test_format_and_store_missing_key_raises(vault):
    with pytest.raises(FormatError, match="not found"):
        format_and_store(vault, "GHOST", "lower")
