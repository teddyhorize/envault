"""Vault module: read/write encrypted .env secret files."""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from envault.crypto import encrypt, decrypt

DEFAULT_VAULT_FILE = ".envault"


class VaultError(Exception):
    """Raised for vault-level errors."""


class Vault:
    """Manages a collection of encrypted secrets stored in a single vault file."""

    def __init__(self, path: str = DEFAULT_VAULT_FILE, password: str = "") -> None:
        self.path = Path(path)
        self._password = password
        self._secrets: Dict[str, str] = {}

        if self.path.exists():
            self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set(self, key: str, value: str) -> None:
        """Add or update a secret."""
        if not key:
            raise VaultError("Secret key must not be empty.")
        self._secrets[key] = value
        self._save()

    def get(self, key: str) -> Optional[str]:
        """Return the plaintext value for *key*, or None if not found."""
        return self._secrets.get(key)

    def delete(self, key: str) -> bool:
        """Remove a secret.  Returns True if it existed, False otherwise."""
        existed = key in self._secrets
        if existed:
            del self._secrets[key]
            self._save()
        return existed

    def list_keys(self) -> list:
        """Return a sorted list of all secret keys."""
        return sorted(self._secrets.keys())

    def export_env(self) -> str:
        """Return all secrets formatted as KEY=VALUE lines."""
        lines = [f"{k}={v}" for k, v in sorted(self._secrets.items())]
        return os.linesep.join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save(self) -> None:
        plaintext = json.dumps(self._secrets)
        token = encrypt(plaintext, self._password)
        self.path.write_text(token, encoding="utf-8")

    def _load(self) -> None:
        token = self.path.read_text(encoding="utf-8").strip()
        try:
            plaintext = decrypt(token, self._password)
        except Exception as exc:
            raise VaultError(f"Failed to unlock vault '{self.path}': {exc}") from exc
        self._secrets = json.loads(plaintext)
