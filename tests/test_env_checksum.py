"""Tests for envault.env_checksum."""

import pytest

from envault.env_checksum import ChecksumError, compute_checksum, verify_checksum
from envault.vault import Vault


PASSWORD = "test-password"


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.db"), PASSWORD)
    v.set("API_KEY", "abc123", PASSWORD)
    v.set("DB_URL", "postgres://localhost/db", PASSWORD)
    v.set("SECRET", "s3cr3t", PASSWORD)
    return v


@pytest.fixture
def empty_vault(tmp_path):
    return Vault(str(tmp_path / "empty.db"), PASSWORD)


def test_compute_checksum_returns_string(vault):
    result = compute_checksum(vault, PASSWORD)
    assert isinstance(result, str)
    assert len(result) > 0


def test_compute_checksum_is_deterministic(vault):
    first = compute_checksum(vault, PASSWORD)
    second = compute_checksum(vault, PASSWORD)
    assert first == second


def test_compute_checksum_changes_when_value_changes(vault):
    before = compute_checksum(vault, PASSWORD)
    vault.set("API_KEY", "new-value", PASSWORD)
    after = compute_checksum(vault, PASSWORD)
    assert before != after


def test_compute_checksum_changes_when_key_added(vault):
    before = compute_checksum(vault, PASSWORD)
    vault.set("NEW_KEY", "new-value", PASSWORD)
    after = compute_checksum(vault, PASSWORD)
    assert before != after


def test_compute_checksum_changes_when_key_deleted(vault):
    before = compute_checksum(vault, PASSWORD)
    vault.delete("SECRET")
    after = compute_checksum(vault, PASSWORD)
    assert before != after


def test_compute_checksum_empty_vault(empty_vault):
    result = compute_checksum(empty_vault, PASSWORD)
    assert isinstance(result, str)
    assert len(result) == 64  # sha256 hex digest length


def test_compute_checksum_sha512_algorithm(vault):
    result = compute_checksum(vault, PASSWORD, algorithm="sha512")
    assert len(result) == 128  # sha512 hex digest length


def test_compute_checksum_unsupported_algorithm_raises(vault):
    with pytest.raises(ChecksumError, match="Unsupported hash algorithm"):
        compute_checksum(vault, PASSWORD, algorithm="not-a-real-algo")


def test_verify_checksum_returns_true_when_unchanged(vault):
    checksum = compute_checksum(vault, PASSWORD)
    assert verify_checksum(vault, PASSWORD, checksum) is True


def test_verify_checksum_returns_false_after_change(vault):
    checksum = compute_checksum(vault, PASSWORD)
    vault.set("API_KEY", "tampered", PASSWORD)
    assert verify_checksum(vault, PASSWORD, checksum) is False


def test_verify_checksum_returns_false_for_wrong_expected(vault):
    assert verify_checksum(vault, PASSWORD, "deadbeef") is False
