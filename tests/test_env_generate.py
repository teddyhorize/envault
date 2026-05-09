"""Tests for envault.env_generate."""

import string
import pytest

from envault.env_generate import (
    GenerateError,
    generate_secret,
    generate_and_store,
    ALPHABET_ALPHANUMERIC,
    ALPHABET_HEX,
    ALPHABET_NUMERIC,
)
from envault.vault import Vault


@pytest.fixture
def vault(tmp_path):
    path = str(tmp_path / "test.vault")
    v = Vault(path, password="testpass")
    return v


# --- generate_secret ---

def test_generate_secret_default_length():
    result = generate_secret()
    assert len(result) == 32


def test_generate_secret_custom_length():
    result = generate_secret(length=16)
    assert len(result) == 16


def test_generate_secret_returns_string():
    result = generate_secret()
    assert isinstance(result, str)


def test_generate_secret_alphanumeric_charset():
    result = generate_secret(length=100, charset="alphanumeric")
    allowed = set(ALPHABET_ALPHANUMERIC)
    assert all(c in allowed for c in result)


def test_generate_secret_hex_charset():
    result = generate_secret(length=64, charset="hex")
    allowed = set(ALPHABET_HEX)
    assert all(c in allowed for c in result)


def test_generate_secret_numeric_charset():
    result = generate_secret(length=20, charset="numeric")
    assert result.isdigit()


def test_generate_secret_custom_alphabet():
    result = generate_secret(length=50, charset="abc")
    assert all(c in "abc" for c in result)


def test_generate_secret_zero_length_raises():
    with pytest.raises(GenerateError, match="Length must be at least 1"):
        generate_secret(length=0)


def test_generate_secret_negative_length_raises():
    with pytest.raises(GenerateError):
        generate_secret(length=-5)


def test_generate_secret_empty_charset_raises():
    with pytest.raises(GenerateError, match="Charset"):
        generate_secret(charset="")


def test_generate_secret_produces_different_values():
    a = generate_secret(length=32)
    b = generate_secret(length=32)
    # Extremely unlikely to collide
    assert a != b


# --- generate_and_store ---

def test_generate_and_store_saves_to_vault(vault):
    value = generate_and_store(vault, "MY_SECRET")
    assert vault.get("MY_SECRET") == value


def test_generate_and_store_returns_generated_value(vault):
    value = generate_and_store(vault, "TOKEN", length=24)
    assert len(value) == 24


def test_generate_and_store_existing_key_raises_without_overwrite(vault):
    vault.set("EXISTING", "old_value")
    with pytest.raises(GenerateError, match="already exists"):
        generate_and_store(vault, "EXISTING")


def test_generate_and_store_overwrite_replaces_value(vault):
    vault.set("KEY", "old")
    new_value = generate_and_store(vault, "KEY", overwrite=True)
    assert vault.get("KEY") == new_value
    assert vault.get("KEY") != "old"


def test_generate_and_store_empty_key_raises(vault):
    with pytest.raises(GenerateError, match="Key must not be empty"):
        generate_and_store(vault, "")
