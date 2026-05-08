"""Watch vault for external changes and trigger callbacks."""
from __future__ import annotations

import os
import time
import threading
from dataclasses import dataclass, field
from typing import Callable, Dict, Optional

from envault.vault import Vault


class WatchError(Exception):
    """Raised when a watch operation fails."""


@dataclass
class WatchEvent:
    """Represents a detected change in the vault file."""
    vault_path: str
    old_mtime: float
    new_mtime: float

    def __repr__(self) -> str:
        return f"WatchEvent(vault_path={self.vault_path!r}, old_mtime={self.old_mtime}, new_mtime={self.new_mtime})"


class VaultWatcher:
    """Polls a vault file for modifications and fires registered callbacks."""

    def __init__(self, vault: Vault, interval: float = 2.0) -> None:
        if not os.path.exists(vault.path):
            raise WatchError(f"Vault file not found: {vault.path}")
        self._vault = vault
        self._interval = interval
        self._callbacks: list[Callable[[WatchEvent], None]] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._last_mtime: float = os.path.getmtime(vault.path)

    def on_change(self, callback: Callable[[WatchEvent], None]) -> None:
        """Register a callback to be invoked when the vault changes."""
        self._callbacks.append(callback)

    def _poll(self) -> None:
        while not self._stop_event.is_set():
            time.sleep(self._interval)
            try:
                current_mtime = os.path.getmtime(self._vault.path)
            except OSError:
                continue
            if current_mtime != self._last_mtime:
                event = WatchEvent(
                    vault_path=self._vault.path,
                    old_mtime=self._last_mtime,
                    new_mtime=current_mtime,
                )
                self._last_mtime = current_mtime
                for cb in self._callbacks:
                    try:
                        cb(event)
                    except Exception:
                        pass

    def start(self) -> None:
        """Start the background polling thread."""
        if self._thread and self._thread.is_alive():
            raise WatchError("Watcher is already running.")
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background polling thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=self._interval + 1)
            self._thread = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()
