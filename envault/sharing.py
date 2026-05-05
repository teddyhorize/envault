"""Team sharing support: export/import encrypted vault bundles."""

import json
import base64
from pathlib import Path
from typing import Optional

from envault.crypto import derive_key, encrypt, decrypt
from envault.vault import Vault, VaultError


class SharingError(Exception):
    """Raised when a sharing operation fails."""


BUNDLE_VERSION = 1


def export_bundle(vault: Vault, vault_password: str, share_password: str) -> str:
    """Export all secrets as a portable encrypted bundle string.

    The bundle is re-encrypted with *share_password* so it can be safely
    transmitted to a team member without exposing the vault password.

    Returns a base64-encoded JSON string.
    """
    keys = vault.list_keys()
    if not keys:
        raise SharingError("Vault is empty; nothing to export.")

    plaintext_map = {}
    for key in keys:
        value = vault.get(key, vault_password)
        if value is not None:
            plaintext_map[key] = value

    payload = json.dumps(plaintext_map)
    token = encrypt(payload, share_password)

    bundle = json.dumps({"version": BUNDLE_VERSION, "token": token})
    return base64.b64encode(bundle.encode()).decode()


def import_bundle(
    bundle_str: str,
    share_password: str,
    target_vault: Vault,
    vault_password: str,
    overwrite: bool = False,
) -> list[str]:
    """Import secrets from a bundle into *target_vault*.

    Returns the list of keys that were imported.
    Raises SharingError on format or decryption errors.
    """
    try:
        raw = base64.b64decode(bundle_str.encode()).decode()
        bundle = json.loads(raw)
    except Exception as exc:
        raise SharingError(f"Invalid bundle format: {exc}") from exc

    if bundle.get("version") != BUNDLE_VERSION:
        raise SharingError("Unsupported bundle version.")

    try:
        payload = decrypt(bundle["token"], share_password)
    except Exception as exc:
        raise SharingError(f"Failed to decrypt bundle: {exc}") from exc

    try:
        secret_map: dict = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise SharingError(f"Bundle payload is corrupted: {exc}") from exc

    imported: list[str] = []
    for key, value in secret_map.items():
        if not overwrite and target_vault.get(key, vault_password) is not None:
            continue
        target_vault.set(key, value, vault_password)
        imported.append(key)

    return imported
