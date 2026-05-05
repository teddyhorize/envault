"""Tests for envault.sharing — team bundle export/import."""

import pytest

from envault.vault import Vault
from envault.sharing import export_bundle, import_bundle, SharingError


VAULT_PASS = "vault-secret"
SHARE_PASS = "share-secret"


@pytest.fixture
def populated_vault(tmp_path):
    v = Vault(tmp_path / "vault.json")
    v.set("DB_URL", "postgres://localhost/db", VAULT_PASS)
    v.set("API_KEY", "abc123", VAULT_PASS)
    return v


@pytest.fixture
def empty_vault(tmp_path):
    return Vault(tmp_path / "empty.json")


@pytest.fixture
def target_vault(tmp_path):
    return Vault(tmp_path / "target.json")


def test_export_returns_string(populated_vault):
    bundle = export_bundle(populated_vault, VAULT_PASS, SHARE_PASS)
    assert isinstance(bundle, str)
    assert len(bundle) > 0


def test_export_empty_vault_raises(empty_vault):
    with pytest.raises(SharingError, match="empty"):
        export_bundle(empty_vault, VAULT_PASS, SHARE_PASS)


def test_import_recovers_all_secrets(populated_vault, target_vault):
    bundle = export_bundle(populated_vault, VAULT_PASS, SHARE_PASS)
    imported = import_bundle(bundle, SHARE_PASS, target_vault, VAULT_PASS)

    assert set(imported) == {"DB_URL", "API_KEY"}
    assert target_vault.get("DB_URL", VAULT_PASS) == "postgres://localhost/db"
    assert target_vault.get("API_KEY", VAULT_PASS) == "abc123"


def test_import_wrong_share_password_raises(populated_vault, target_vault):
    bundle = export_bundle(populated_vault, VAULT_PASS, SHARE_PASS)
    with pytest.raises(SharingError, match="decrypt"):
        import_bundle(bundle, "wrong-password", target_vault, VAULT_PASS)


def test_import_corrupted_bundle_raises(target_vault):
    with pytest.raises(SharingError, match="Invalid bundle format"):
        import_bundle("not-valid-base64!!!", SHARE_PASS, target_vault, VAULT_PASS)


def test_import_no_overwrite_by_default(populated_vault, target_vault):
    target_vault.set("API_KEY", "original", VAULT_PASS)
    bundle = export_bundle(populated_vault, VAULT_PASS, SHARE_PASS)
    imported = import_bundle(bundle, SHARE_PASS, target_vault, VAULT_PASS)

    assert "API_KEY" not in imported
    assert target_vault.get("API_KEY", VAULT_PASS) == "original"


def test_import_overwrite_replaces_existing(populated_vault, target_vault):
    target_vault.set("API_KEY", "original", VAULT_PASS)
    bundle = export_bundle(populated_vault, VAULT_PASS, SHARE_PASS)
    imported = import_bundle(bundle, SHARE_PASS, target_vault, VAULT_PASS, overwrite=True)

    assert "API_KEY" in imported
    assert target_vault.get("API_KEY", VAULT_PASS) == "abc123"


def test_roundtrip_preserves_special_characters(tmp_path, target_vault):
    src = Vault(tmp_path / "src.json")
    src.set("SPECIAL", 'p@$$w0rd!#&={}"', VAULT_PASS)
    bundle = export_bundle(src, VAULT_PASS, SHARE_PASS)
    import_bundle(bundle, SHARE_PASS, target_vault, VAULT_PASS)
    assert target_vault.get("SPECIAL", VAULT_PASS) == 'p@$$w0rd!#&={}"'
