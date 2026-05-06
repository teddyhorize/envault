"""CLI commands for managing vault operation hooks."""
from __future__ import annotations

import argparse
import sys

from envault.hooks import HooksError, list_hooks, register_hook, unregister_hook
from envault.vault import Vault, VaultError


def _open_vault(vault_path: str, password: str) -> Vault:
    try:
        return Vault(vault_path, password=password)
    except VaultError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_hook_add(args: argparse.Namespace) -> None:
    """Register a new hook command for an event."""
    _open_vault(args.vault, args.password)
    try:
        register_hook(args.vault, args.event, args.command)
        print(f"[ok] Hook registered for '{args.event}': {args.command}")
    except HooksError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_hook_remove(args: argparse.Namespace) -> None:
    """Unregister a hook command from an event."""
    _open_vault(args.vault, args.password)
    try:
        removed = unregister_hook(args.vault, args.event, args.command)
        if removed:
            print(f"[ok] Hook removed from '{args.event}': {args.command}")
        else:
            print(f"[warn] Hook not found for '{args.event}': {args.command}")
    except HooksError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_hook_list(args: argparse.Namespace) -> None:
    """List all registered hooks, optionally filtered by event."""
    _open_vault(args.vault, args.password)
    event = getattr(args, "event", None) or None
    try:
        hooks = list_hooks(args.vault, event)
    except HooksError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)

    any_found = False
    for ev, commands in hooks.items():
        if commands:
            any_found = True
            print(f"{ev}:")
            for cmd in commands:
                print(f"  - {cmd}")
    if not any_found:
        print("No hooks registered.")


def build_hooks_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("hooks", help="Manage vault operation hooks")
    sp = p.add_subparsers(dest="hooks_cmd", required=True)

    add_p = sp.add_parser("add", help="Register a hook")
    add_p.add_argument("event", choices=["pre_set", "post_set", "pre_get", "post_get", "pre_delete", "post_delete"])
    add_p.add_argument("command", help="Shell command to run")
    add_p.set_defaults(func=cmd_hook_add)

    rm_p = sp.add_parser("remove", help="Unregister a hook")
    rm_p.add_argument("event", choices=["pre_set", "post_set", "pre_get", "post_get", "pre_delete", "post_delete"])
    rm_p.add_argument("command", help="Shell command to remove")
    rm_p.set_defaults(func=cmd_hook_remove)

    ls_p = sp.add_parser("list", help="List registered hooks")
    ls_p.add_argument("--event", default=None, help="Filter by event name")
    ls_p.set_defaults(func=cmd_hook_list)


def _hooks_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("Use 'hooks add', 'hooks remove', or 'hooks list'.")
