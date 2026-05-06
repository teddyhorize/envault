"""CLI commands for importing/exporting .env files."""
from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envault.vault import Vault, VaultError
from envault.import_export_env import EnvFileError, export_to_env_file, import_from_env_file


def _open_vault(vault_path: str, password: str) -> Vault:
    try:
        return Vault(vault_path, password=password)
    except VaultError as exc:
        print(f"[error] Cannot open vault: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_import_env(args: argparse.Namespace) -> None:
    """Import secrets from a .env file into the vault."""
    vault = _open_vault(args.vault, args.password)
    try:
        imported = import_from_env_file(
            vault,
            args.env_file,
            overwrite=not args.no_overwrite,
        )
    except (EnvFileError, FileNotFoundError) as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Imported {len(imported)} secret(s): {', '.join(imported)}")


def cmd_export_env(args: argparse.Namespace) -> None:
    """Export secrets from the vault to a .env file."""
    vault = _open_vault(args.vault, args.password)
    keys: Optional[List[str]] = args.keys if args.keys else None
    try:
        exported = export_to_env_file(vault, args.env_file, keys=keys)
    except EnvFileError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)
    print(f"Exported {len(exported)} secret(s) to {args.env_file!r}")


def build_env_file_parser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    # --- import ---
    p_import = subparsers.add_parser(
        "import-env",
        help="Import secrets from a .env file",
    )
    p_import.add_argument("vault", help="Path to the vault file")
    p_import.add_argument("env_file", help="Path to the .env file to import")
    p_import.add_argument("--password", required=True, help="Vault password")
    p_import.add_argument(
        "--no-overwrite",
        action="store_true",
        default=False,
        help="Skip keys that already exist in the vault",
    )
    p_import.set_defaults(func=cmd_import_env)

    # --- export ---
    p_export = subparsers.add_parser(
        "export-env",
        help="Export secrets to a .env file",
    )
    p_export.add_argument("vault", help="Path to the vault file")
    p_export.add_argument("env_file", help="Destination .env file path")
    p_export.add_argument("--password", required=True, help="Vault password")
    p_export.add_argument(
        "--keys",
        nargs="+",
        default=[],
        help="Specific keys to export (default: all)",
    )
    p_export.set_defaults(func=cmd_export_env)


def _env_file_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("Use 'import-env' or 'export-env' subcommand.", file=sys.stderr)
        sys.exit(1)
