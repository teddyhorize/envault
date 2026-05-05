"""Tests for envault.crypto encryption/decryption module."""

import pytest
from envault.crypto import encrypt, decrypt


PASSWORD = "super-secret-passphrase"
PLAINTEXT = "MY_API_KEY=abc123xyz"


def test_encrypt_returns_string():
    token = encrypt(PLAINTEXT, PASSWORD)
    assert isinstance(token, str)
    assert len(token) > 0


def test_encrypt_produces_different_tokens():
    """Each encryption call should produce a unique token (random salt/nonce)."""
    token1 = encrypt(PLAINTEXT, PASSWORD)
    token2 = encrypt(PLAINTEXT, PASSWORD)
    assert token1 != token2


def test_decrypt_recovers_plaintext():
    token = encrypt(PLAINTEXT, PASSWORD)
    result = decrypt(token, PASSWORD)
    assert result == PLAINTEXT


def test_decrypt_wrong_password_raises():
    token = encrypt(PLAINTEXT, PASSWORD)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(token, "wrong-password")


def test_decrypt_corrupted_token_raises():
    token = encrypt(PLAINTEXT, PASSWORD)
    corrupted = token[:-4] + "XXXX"
    with pytest.raises(ValueError):
        decrypt(corrupted, PASSWORD)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(ValueError, match="Invalid token format"):
        decrypt("!!!not-base64!!!", PASSWORD)


def test_decrypt_too_short_token_raises():
    import base64
    short = base64.urlsafe_b64encode(b"tooshort").decode()
    with pytest.raises(ValueError, match="too short"):
        decrypt(short, PASSWORD)


def test_roundtrip_special_characters():
    special = "SECRET=p@$$w0rd!#&*()\nANOTHER=val\u00e9"
    token = encrypt(special, PASSWORD)
    assert decrypt(token, PASSWORD) == special
