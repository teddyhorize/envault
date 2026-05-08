"""CLI commands for renaming vault secrets."""

from __future__ import annotations

import argparse
import sys

from envault.vault import Vault, VaultError
from envault.env_rename import RenameError, rename_secret, rename_prefix


def _open_vault(path: str, password: str) -> Vault:
    try:
        return Vault(path, password=password)
    except VaultError as exc:
        print(f"[envault] error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_rename(args: argparse.Namespace) -> None:
    """Rename a single secret key."""
    vault = _open_vault(args.vault, args.password)
    try:
        rename_secret(vault, args.old_key, args.new_key, overwrite=args.overwrite)
    except RenameError as exc:
        print(f"[envault] rename error: {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Renamed {args.old_key!r} -> {args.new_key!r}")


def cmd_rename_prefix(args: argparse.Namespace) -> None:
    """Rename all secrets sharing a common prefix."""
    vault = _open_vault(args.vault, args.password)
    try:
        pairs = rename_prefix(vault, args.old_prefix, args.new_prefix, overwrite=args.overwrite)
    except RenameError as exc:
        print(f"[envault] rename-prefix error: {exc}", file=sys.stderr)
        sys.exit(1)
    for old_key, new_key in pairs:
        print(f"  {old_key!r} -> {new_key!r}")
    print(f"Renamed {len(pairs)} key(s).")


def build_rename_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register *rename* and *rename-prefix* sub-commands onto *subparsers*."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--vault", required=True, help="Path to vault file")
    common.add_argument("--password", required=True, help="Vault password")
    common.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Overwrite target key if it already exists",
    )

    p_rename = subparsers.add_parser("rename", parents=[common], help="Rename a single secret")
    p_rename.add_argument("old_key", help="Existing key name")
    p_rename.add_argument("new_key", help="New key name")
    p_rename.set_defaults(func=cmd_rename)

    p_prefix = subparsers.add_parser(
        "rename-prefix", parents=[common], help="Rename all secrets sharing a prefix"
    )
    p_prefix.add_argument("old_prefix", help="Existing key prefix")
    p_prefix.add_argument("new_prefix", help="Replacement prefix")
    p_prefix.set_defaults(func=cmd_rename_prefix)


def _rename_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("Use 'rename' or 'rename-prefix'. See --help.", file=sys.stderr)
        sys.exit(1)


def main() -> None:  # pragma: no cover
    parser = argparse.ArgumentParser(description="envault rename commands")
    subparsers = parser.add_subparsers(dest="command")
    build_rename_parser(subparsers)
    args = parser.parse_args()
    _rename_command_handler(args)


if __name__ == "__main__":  # pragma: no cover
    main()
