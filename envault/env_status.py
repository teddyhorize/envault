"""Vault status reporting: expiry, pins, locks, and key health summary."""

from dataclasses import dataclass, field
from typing import List, Optional
import datetime

from envault.vault import Vault, VaultError
from envault.expiry import get_expiry, is_expired
from envault.env_pin import get_pinned
from envault.env_lock import is_locked


class StatusError(Exception):
    pass


@dataclass
class KeyStatus:
    key: str
    pinned: bool = False
    expired: bool = False
    expiry_ts: Optional[float] = None

    def __repr__(self) -> str:
        parts = [f"KeyStatus(key={self.key!r}"]
        if self.pinned:
            parts.append("pinned")
        if self.expired:
            parts.append("EXPIRED")
        elif self.expiry_ts:
            dt = datetime.datetime.fromtimestamp(self.expiry_ts)
            parts.append(f"expires={dt.strftime('%Y-%m-%d')}")
        return ", ".join(parts) + ")"


@dataclass
class VaultStatus:
    vault_path: str
    total_keys: int
    locked: bool
    pinned_keys: List[str] = field(default_factory=list)
    expired_keys: List[str] = field(default_factory=list)
    key_statuses: List[KeyStatus] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Vault : {self.vault_path}",
            f"Keys  : {self.total_keys}",
            f"Locked: {self.locked}",
            f"Pinned: {len(self.pinned_keys)}",
            f"Expired: {len(self.expired_keys)}",
        ]
        return "\n".join(lines)


def get_vault_status(vault: Vault) -> VaultStatus:
    """Collect status information for all keys in a vault."""
    try:
        keys = vault.list()
    except VaultError as exc:
        raise StatusError(f"Failed to list vault keys: {exc}") from exc

    locked = is_locked(vault.path)
    pinned = set(get_pinned(vault))

    key_statuses = []
    expired_keys = []

    for key in keys:
        exp_ts = get_expiry(vault, key)
        expired = is_expired(vault, key) if exp_ts is not None else False
        ks = KeyStatus(
            key=key,
            pinned=key in pinned,
            expired=expired,
            expiry_ts=exp_ts,
        )
        key_statuses.append(ks)
        if expired:
            expired_keys.append(key)

    return VaultStatus(
        vault_path=vault.path,
        total_keys=len(keys),
        locked=locked,
        pinned_keys=list(pinned),
        expired_keys=expired_keys,
        key_statuses=key_statuses,
    )
