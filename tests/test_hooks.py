"""Tests for envault/hooks.py."""
from __future__ import annotations

import pytest

from envault.hooks import (
    HOOK_EVENTS,
    HooksError,
    list_hooks,
    register_hook,
    run_hooks,
    unregister_hook,
)
from envault.vault import Vault


@pytest.fixture
def vault(tmp_path):
    v = Vault(str(tmp_path / "test.vault"), password="secret")
    v.set("KEY", "value")
    return v


def test_register_hook_adds_command(vault):
    register_hook(vault.path, "post_set", "echo set")
    hooks = list_hooks(vault.path, "post_set")
    assert "echo set" in hooks["post_set"]


def test_register_hook_duplicate_is_idempotent(vault):
    register_hook(vault.path, "post_set", "echo set")
    register_hook(vault.path, "post_set", "echo set")
    hooks = list_hooks(vault.path, "post_set")
    assert hooks["post_set"].count("echo set") == 1


def test_register_hook_invalid_event_raises(vault):
    with pytest.raises(HooksError, match="Unknown event"):
        register_hook(vault.path, "on_explode", "echo boom")


def test_register_hook_empty_command_raises(vault):
    with pytest.raises(HooksError, match="must not be empty"):
        register_hook(vault.path, "post_set", "   ")


def test_unregister_hook_removes_command(vault):
    register_hook(vault.path, "pre_delete", "echo deleting")
    removed = unregister_hook(vault.path, "pre_delete", "echo deleting")
    assert removed is True
    hooks = list_hooks(vault.path, "pre_delete")
    assert "echo deleting" not in hooks["pre_delete"]


def test_unregister_hook_missing_returns_false(vault):
    result = unregister_hook(vault.path, "pre_delete", "echo nonexistent")
    assert result is False


def test_unregister_hook_invalid_event_raises(vault):
    with pytest.raises(HooksError, match="Unknown event"):
        unregister_hook(vault.path, "bad_event", "echo x")


def test_list_hooks_returns_all_events(vault):
    hooks = list_hooks(vault.path)
    for event in HOOK_EVENTS:
        assert event in hooks


def test_list_hooks_filtered_by_event(vault):
    register_hook(vault.path, "post_get", "echo got")
    hooks = list_hooks(vault.path, "post_get")
    assert list(hooks.keys()) == ["post_get"]
    assert "echo got" in hooks["post_get"]


def test_list_hooks_invalid_event_raises(vault):
    with pytest.raises(HooksError, match="Unknown event"):
        list_hooks(vault.path, "invalid")


def test_run_hooks_calls_runner(vault):
    register_hook(vault.path, "post_set", "echo hello")
    called = []
    run_hooks(vault.path, "post_set", runner=called.append)
    assert called == ["echo hello"]


def test_run_hooks_no_hooks_returns_empty(vault):
    result = run_hooks(vault.path, "pre_get", runner=lambda _: None)
    assert result == []


def test_run_hooks_multiple_commands_in_order(vault):
    register_hook(vault.path, "post_delete", "cmd_one")
    register_hook(vault.path, "post_delete", "cmd_two")
    called = []
    run_hooks(vault.path, "post_delete", runner=called.append)
    assert called == ["cmd_one", "cmd_two"]
