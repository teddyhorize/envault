"""CLI commands for vault snapshot and restore."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.vault import Vault
from envault.snapshot import SnapshotError, create_snapshot, restore_snapshot


def cmd_snapshot(args: argparse.Namespace) -> None:
    """Create a snapshot of a vault and write it to a file or stdout."""
    try:
        vault = Vault(args.vault, password=args.password)
    except Exception as exc:  # noqa: BLE001
        print(f"Error opening vault: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        snapshot_data = create_snapshot(vault)
    except SnapshotError as exc:
        print(f"Snapshot error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.output:
        Path(args.output).write_text(snapshot_data, encoding="utf-8")
        print(f"Snapshot written to {args.output}")
    else:
        print(snapshot_data)


def cmd_restore(args: argparse.Namespace) -> None:
    """Restore secrets from a snapshot file into a vault."""
    try:
        snapshot_data = Path(args.snapshot_file).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"Cannot read snapshot file: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        vault = Vault(args.vault, password=args.password)
    except Exception as exc:  # noqa: BLE001
        print(f"Error opening vault: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        written = restore_snapshot(vault, snapshot_data, overwrite=args.overwrite)
    except SnapshotError as exc:
        print(f"Restore error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Restored {written} secret(s) into {args.vault}.")


def build_snapshot_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Register snapshot and restore sub-commands."""
    snap_p = subparsers.add_parser("snapshot", help="Create a vault snapshot")
    snap_p.add_argument("vault", help="Path to the source vault file")
    snap_p.add_argument("--password", required=True, help="Vault password")
    snap_p.add_argument("--output", "-o", default=None, help="Output file (default: stdout)")
    snap_p.set_defaults(func=cmd_snapshot)

    restore_p = subparsers.add_parser("restore", help="Restore secrets from a snapshot")
    restore_p.add_argument("vault", help="Path to the target vault file")
    restore_p.add_argument("snapshot_file", help="Path to the snapshot JSON file")
    restore_p.add_argument("--password", required=True, help="Vault password")
    restore_p.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite existing keys in the target vault",
    )
    restore_p.set_defaults(func=cmd_restore)


def _snapshot_command_handler(argv: list[str] | None = None) -> None:
    """Standalone entry-point for snapshot commands."""
    parser = argparse.ArgumentParser(prog="envault-snapshot", description="Vault snapshot tools")
    subparsers = parser.add_subparsers(dest="command")
    build_snapshot_parser(subparsers)
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(0)
    args.func(args)
