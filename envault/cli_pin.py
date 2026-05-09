"""CLI commands for secret pinning."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.vault import Vault, VaultError
from envault.env_pin import PinError, pin_secret, unpin_secret, is_pinned, list_pinned


def _open_vault(path: str, password: str) -> Vault:
    try:
        return Vault(path, password=password)
    except VaultError as e:
        print(f"[error] Could not open vault: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"[error] Vault file not found: {path}", file=sys.stderr)
        sys.exit(1)


def cmd_pin(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        pin_secret(vault, args.key)
        print(f"[ok] Key '{args.key}' is now pinned.")
    except PinError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_unpin(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        unpin_secret(vault, args.key)
        print(f"[ok] Key '{args.key}' has been unpinned.")
    except PinError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_pin_list(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    pinned = list_pinned(vault)
    if not pinned:
        print("No pinned secrets.")
    else:
        print(f"Pinned secrets ({len(pinned)}):")
        for key in pinned:
            print(f"  - {key}")


def build_pin_parser(subparsers: argparse._SubParsersAction) -> None:
    pin_parser = subparsers.add_parser("pin", help="Pin a secret to protect it.")
    pin_parser.add_argument("vault", help="Path to vault file")
    pin_parser.add_argument("password", help="Vault password")
    pin_parser.add_argument("key", help="Secret key to pin")
    pin_parser.set_defaults(func=cmd_pin)

    unpin_parser = subparsers.add_parser("unpin", help="Unpin a secret.")
    unpin_parser.add_argument("vault", help="Path to vault file")
    unpin_parser.add_argument("password", help="Vault password")
    unpin_parser.add_argument("key", help="Secret key to unpin")
    unpin_parser.set_defaults(func=cmd_unpin)

    list_parser = subparsers.add_parser("pin-list", help="List all pinned secrets.")
    list_parser.add_argument("vault", help="Path to vault file")
    list_parser.add_argument("password", help="Vault password")
    list_parser.set_defaults(func=cmd_pin_list)


def _pin_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("No pin subcommand given. Use pin, unpin, or pin-list.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="Envault secret pinning")
    subparsers = parser.add_subparsers()
    build_pin_parser(subparsers)
    args = parser.parse_args()
    _pin_command_handler(args)


if __name__ == "__main__":
    main()
