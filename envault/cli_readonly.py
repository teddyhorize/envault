"""CLI commands for read-only secret protection."""

import argparse
import sys
from envault.vault import Vault, VaultError
from envault.env_readonly import (
    ReadOnlyError,
    protect,
    unprotect,
    is_protected,
    list_protected,
)


def _open_vault(args):
    try:
        return Vault(args.vault, args.password)
    except VaultError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: Vault file not found: {args.vault}", file=sys.stderr)
        sys.exit(1)


def cmd_protect(args):
    vault = _open_vault(args)
    try:
        protect(vault, args.key)
        print(f"Key '{args.key}' is now read-only protected.")
    except ReadOnlyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_unprotect(args):
    vault = _open_vault(args)
    try:
        unprotect(vault, args.key)
        print(f"Read-only protection removed from '{args.key}'.")
    except ReadOnlyError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_readonly_list(args):
    vault = _open_vault(args)
    keys = list_protected(vault)
    if not keys:
        print("No read-only protected keys.")
    else:
        print(f"Read-only protected keys ({len(keys)}):")
        for key in keys:
            print(f"  {key}")


def cmd_readonly_status(args):
    vault = _open_vault(args)
    protected = is_protected(vault, args.key)
    status = "read-only" if protected else "writable"
    print(f"Key '{args.key}': {status}")


def build_readonly_parser(subparsers):
    p = subparsers.add_parser("readonly", help="Manage read-only protection for secrets")
    p.add_argument("--vault", required=True, help="Path to vault file")
    p.add_argument("--password", required=True, help="Vault password")
    sub = p.add_subparsers(dest="readonly_cmd", required=True)

    sp = sub.add_parser("protect", help="Mark a key as read-only")
    sp.add_argument("key", help="Secret key to protect")
    sp.set_defaults(func=cmd_protect)

    su = sub.add_parser("unprotect", help="Remove read-only protection")
    su.add_argument("key", help="Secret key to unprotect")
    su.set_defaults(func=cmd_unprotect)

    sub.add_parser("list", help="List all protected keys").set_defaults(func=cmd_readonly_list)

    ss = sub.add_parser("status", help="Check protection status of a key")
    ss.add_argument("key", help="Secret key to check")
    ss.set_defaults(func=cmd_readonly_status)

    return p


def _readonly_command_handler(args):
    args.func(args)


def main():
    parser = argparse.ArgumentParser(description="envault readonly protection")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_readonly_parser(subparsers)
    args = parser.parse_args()
    _readonly_command_handler(args)


if __name__ == "__main__":
    main()
