"""Pre/post hooks for vault operations (set, get, delete)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List, Optional

HOOK_EVENTS = ("pre_set", "post_set", "pre_get", "post_get", "pre_delete", "post_delete")


class HooksError(Exception):
    """Raised when a hook operation fails."""


def _hooks_path(vault_path: str) -> Path:
    return Path(vault_path).with_suffix(".hooks.json")


def _load_hooks(vault_path: str) -> Dict[str, List[str]]:
    p = _hooks_path(vault_path)
    if not p.exists():
        return {event: [] for event in HOOK_EVENTS}
    try:
        data = json.loads(p.read_text())
        for event in HOOK_EVENTS:
            data.setdefault(event, [])
        return data
    except (json.JSONDecodeError, OSError) as exc:
        raise HooksError(f"Failed to load hooks: {exc}") from exc


def _save_hooks(vault_path: str, hooks: Dict[str, List[str]]) -> None:
    p = _hooks_path(vault_path)
    try:
        p.write_text(json.dumps(hooks, indent=2))
    except OSError as exc:
        raise HooksError(f"Failed to save hooks: {exc}") from exc


def register_hook(vault_path: str, event: str, command: str) -> None:
    """Register a shell command to run on *event*."""
    if event not in HOOK_EVENTS:
        raise HooksError(f"Unknown event '{event}'. Valid events: {HOOK_EVENTS}")
    if not command.strip():
        raise HooksError("Hook command must not be empty.")
    hooks = _load_hooks(vault_path)
    if command not in hooks[event]:
        hooks[event].append(command)
        _save_hooks(vault_path, hooks)


def unregister_hook(vault_path: str, event: str, command: str) -> bool:
    """Remove a hook command. Returns True if it was present."""
    if event not in HOOK_EVENTS:
        raise HooksError(f"Unknown event '{event}'. Valid events: {HOOK_EVENTS}")
    hooks = _load_hooks(vault_path)
    if command in hooks[event]:
        hooks[event].remove(command)
        _save_hooks(vault_path, hooks)
        return True
    return False


def list_hooks(vault_path: str, event: Optional[str] = None) -> Dict[str, List[str]]:
    """Return all hooks, optionally filtered to a single event."""
    hooks = _load_hooks(vault_path)
    if event is not None:
        if event not in HOOK_EVENTS:
            raise HooksError(f"Unknown event '{event}'. Valid events: {HOOK_EVENTS}")
        return {event: hooks[event]}
    return hooks


def run_hooks(
    vault_path: str,
    event: str,
    context: Optional[Dict] = None,
    runner: Optional[Callable[[str], int]] = None,
) -> List[str]:
    """Execute registered hooks for *event*. Returns list of commands run."""
    import subprocess

    hooks = _load_hooks(vault_path)
    commands = hooks.get(event, [])
    env_extra = {f"ENVAULT_{k.upper()}": str(v) for k, v in (context or {}).items()}
    executed = []
    for cmd in commands:
        if runner is not None:
            runner(cmd)
        else:
            import os
            env = {**os.environ, **env_extra}
            subprocess.run(cmd, shell=True, env=env, check=False)
        executed.append(cmd)
    return executed
