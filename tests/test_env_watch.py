"""Tests for envault.env_watch."""
from __future__ import annotations

import os
import time
import pytest

from envault.vault import Vault
from envault.env_watch import VaultWatcher, WatchError, WatchEvent


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "vault.db"), password="watchpass")
    v.set("KEY", "value")
    return v


def test_watcher_starts_and_stops(vault):
    watcher = VaultWatcher(vault, interval=0.1)
    watcher.start()
    assert watcher.is_running()
    watcher.stop()
    assert not watcher.is_running()


def test_watcher_raises_if_vault_missing(tmp_path):
    v = Vault.__new__(Vault)
    v.path = str(tmp_path / "nonexistent.db")
    with pytest.raises(WatchError, match="not found"):
        VaultWatcher(v)


def test_watcher_raises_if_already_running(vault):
    watcher = VaultWatcher(vault, interval=0.1)
    watcher.start()
    try:
        with pytest.raises(WatchError, match="already running"):
            watcher.start()
    finally:
        watcher.stop()


def test_callback_fired_on_change(vault):
    events: list[WatchEvent] = []
    watcher = VaultWatcher(vault, interval=0.05)
    watcher.on_change(events.append)
    watcher.start()
    try:
        time.sleep(0.02)
        # Touch the vault file to simulate an external change
        os.utime(vault.path, None)
        time.sleep(0.2)
    finally:
        watcher.stop()
    assert len(events) >= 1
    assert events[0].vault_path == vault.path


def test_callback_receives_watch_event(vault):
    received: list[WatchEvent] = []
    watcher = VaultWatcher(vault, interval=0.05)
    watcher.on_change(received.append)
    watcher.start()
    try:
        time.sleep(0.02)
        old_mtime = os.path.getmtime(vault.path)
        os.utime(vault.path, None)
        time.sleep(0.2)
    finally:
        watcher.stop()
    assert received
    evt = received[0]
    assert isinstance(evt, WatchEvent)
    assert evt.new_mtime > old_mtime or evt.new_mtime != evt.old_mtime


def test_multiple_callbacks_all_fired(vault):
    results_a: list = []
    results_b: list = []
    watcher = VaultWatcher(vault, interval=0.05)
    watcher.on_change(lambda e: results_a.append(e))
    watcher.on_change(lambda e: results_b.append(e))
    watcher.start()
    try:
        time.sleep(0.02)
        os.utime(vault.path, None)
        time.sleep(0.2)
    finally:
        watcher.stop()
    assert results_a
    assert results_b


def test_watch_event_repr(vault):
    evt = WatchEvent(vault_path=vault.path, old_mtime=1000.0, new_mtime=2000.0)
    r = repr(evt)
    assert "WatchEvent" in r
    assert vault.path in r
