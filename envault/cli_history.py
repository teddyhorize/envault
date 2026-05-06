"""CLI commands for secret version history."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime

from envault.vault import Vault, VaultError
from envault.history import HistoryError, get_versions, get_latest_version, clear_history


def _open_vault(path: str, password: str) -> Vault:
    try:
        return Vault(path, password=password)
    except VaultError as exc:
        print(f"Error opening vault: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_history_show(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        versions = get_versions(vault, args.key)
    except HistoryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not versions:
        print(f"No history found for '{args.key}'.")
        return

    print(f"History for '{args.key}' ({len(versions)} version(s)):")
    for i, entry in enumerate(versions, 1):
        ts = datetime.fromtimestamp(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  [{i}] {ts}  {entry['value']}")


def cmd_history_latest(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        entry = get_latest_version(vault, args.key)
    except HistoryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if entry is None:
        print(f"No history found for '{args.key}'.")
        return

    ts = datetime.fromtimestamp(entry["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
    print(f"{args.key} (latest at {ts}): {entry['value']}")


def cmd_history_clear(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        removed = clear_history(vault, args.key)
    except HistoryError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Cleared {removed} history entry(ies) for '{args.key}'.")


def build_history_parser(subparsers=None):
    if subparsers is None:
        parser = argparse.ArgumentParser(description="Manage secret version history.")
        sub = parser.add_subparsers(dest="history_cmd")
    else:
        parser = subparsers.add_parser("history", help="Secret version history.")
        sub = parser.add_subparsers(dest="history_cmd")

    for cmd_name, func, help_text in [
        ("show", cmd_history_show, "Show all versions of a secret."),
        ("latest", cmd_history_latest, "Show the latest version of a secret."),
        ("clear", cmd_history_clear, "Clear history for a secret."),
    ]:
        p = sub.add_parser(cmd_name, help=help_text)
        p.add_argument("vault", help="Path to vault file.")
        p.add_argument("password", help="Vault password.")
        p.add_argument("key", help="Secret key.")
        p.set_defaults(func=func)

    return parser


def _history_command_handler(args: argparse.Namespace) -> None:
    if not hasattr(args, "func"):
        print("Specify a history sub-command: show, latest, clear", file=sys.stderr)
        sys.exit(1)
    args.func(args)
