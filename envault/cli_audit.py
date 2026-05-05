"""CLI commands for inspecting the vault audit log."""

from __future__ import annotations

import sys
from typing import Optional

from envault.audit import AuditLog


def cmd_audit_log(vault_path: str, last: Optional[int] = None, clear: bool = False) -> None:
    """
    Display or manage the audit log for a vault.

    Args:
        vault_path: Path to the vault file.
        last:       If given, show only the most recent N entries.
        clear:      If True, clear the audit log instead of displaying it.
    """
    log = AuditLog(vault_path)

    if clear:
        log.clear()
        print("Audit log cleared.", file=sys.stdout)
        return

    entries = log.entries()
    if not entries:
        print("No audit entries found.", file=sys.stdout)
        return

    if last is not None:
        entries = entries[-last:]

    _print_entries(entries)


def _print_entries(entries) -> None:
    header = f"{'TIMESTAMP':<30} {'ACTION':<10} {'KEY':<30} {'ACTOR'}"
    separator = "-" * len(header)
    print(header)
    print(separator)
    for entry in entries:
        key_display = entry.key if entry.key is not None else "-"
        print(f"{entry.timestamp:<30} {entry.action:<10} {key_display:<30} {entry.actor}")


def build_audit_parser(subparsers) -> None:
    """Register the 'audit' sub-command on an argparse subparsers object."""
    parser = subparsers.add_parser("audit", help="View the vault audit log")
    parser.add_argument("vault", help="Path to the vault file")
    parser.add_argument(
        "--last",
        type=int,
        metavar="N",
        default=None,
        help="Show only the last N entries",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        default=False,
        help="Clear the audit log",
    )
    parser.set_defaults(func=_audit_command_handler)


def _audit_command_handler(args) -> None:
    cmd_audit_log(
        vault_path=args.vault,
        last=args.last,
        clear=args.clear,
    )
