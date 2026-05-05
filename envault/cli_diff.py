"""CLI commands for vault diff operations."""

from __future__ import annotations
import argparse
import sys
from envault.vault import Vault, VaultError
from envault.diff import diff_vaults, DiffError


def cmd_diff(args: argparse.Namespace) -> None:
    """Compare secrets between two vault files and print a diff summary."""
    try:
        left = Vault(args.left_vault, args.left_password)
        right = Vault(args.right_vault, args.right_password)
        result = diff_vaults(left, args.left_password, right, args.right_password)
    except (VaultError, DiffError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not result.has_differences:
        print("Vaults are identical.")
        return

    print(f"Comparing '{args.left_vault}' <-> '{args.right_vault}'")
    print(result.summary())
    print()
    print(
        f"Summary: {len(result.added)} added, "
        f"{len(result.removed)} removed, "
        f"{len(result.changed)} changed, "
        f"{len(result.unchanged)} unchanged."
    )


def build_diff_parser(subparsers) -> None:
    """Register the 'diff' subcommand."""
    parser = subparsers.add_parser(
        "diff",
        help="Compare secrets between two vault files.",
    )
    parser.add_argument("left_vault", help="Path to the left (base) vault file.")
    parser.add_argument("left_password", help="Password for the left vault.")
    parser.add_argument("right_vault", help="Path to the right (target) vault file.")
    parser.add_argument("right_password", help="Password for the right vault.")
    parser.set_defaults(func=_diff_command_handler)


def _diff_command_handler(args: argparse.Namespace) -> None:
    cmd_diff(args)
