"""CLI commands for TTL management."""

import argparse
import sys
import time
from datetime import datetime

from envault.vault import Vault, VaultError
from envault.env_ttl import (
    TTLError,
    set_ttl,
    get_ttl,
    is_expired,
    clear_ttl,
    list_ttl,
    purge_expired,
)


def _open_vault(args) -> Vault:
    try:
        return Vault(args.vault, password=args.password)
    except FileNotFoundError:
        print(f"Error: vault file '{args.vault}' not found.", file=sys.stderr)
        sys.exit(1)
    except VaultError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_ttl_set(args) -> None:
    vault = _open_vault(args)
    try:
        expiry = set_ttl(vault, args.key, args.seconds)
        ts = datetime.fromtimestamp(expiry).strftime("%Y-%m-%d %H:%M:%S")
        print(f"TTL set for '{args.key}': expires at {ts} ({args.seconds}s).")
    except TTLError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_ttl_get(args) -> None:
    vault = _open_vault(args)
    try:
        info = get_ttl(vault, args.key)
        if info is None:
            print(f"No TTL set for '{args.key}'.")
        else:
            ts = datetime.fromtimestamp(info["expires_at"]).strftime("%Y-%m-%d %H:%M:%S")
            expired = " [EXPIRED]" if is_expired(vault, args.key) else ""
            print(f"Key: {args.key}  TTL: {info['ttl_seconds']}s  Expires: {ts}{expired}")
    except TTLError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_ttl_clear(args) -> None:
    vault = _open_vault(args)
    try:
        removed = clear_ttl(vault, args.key)
        if removed:
            print(f"TTL cleared for '{args.key}'.")
        else:
            print(f"No TTL was set for '{args.key}'.")
    except TTLError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_ttl_list(args) -> None:
    vault = _open_vault(args)
    entries = list_ttl(vault)
    if not entries:
        print("No TTLs set.")
        return
    now = time.time()
    for key, info in sorted(entries.items()):
        ts = datetime.fromtimestamp(info["expires_at"]).strftime("%Y-%m-%d %H:%M:%S")
        status = "EXPIRED" if now >= info["expires_at"] else "active"
        print(f"  {key:<30} {info['ttl_seconds']:>6}s  {ts}  [{status}]")


def cmd_ttl_purge(args) -> None:
    vault = _open_vault(args)
    purged = purge_expired(vault)
    if purged:
        print(f"Purged {len(purged)} expired key(s): {', '.join(purged)}")
    else:
        print("No expired keys to purge.")


def build_ttl_parser(subparsers=None):
    if subparsers is None:
        parser = argparse.ArgumentParser(description="Manage secret TTLs")
        sub = parser.add_subparsers(dest="ttl_cmd")
    else:
        parser = subparsers.add_parser("ttl", help="Manage secret TTLs")
        sub = parser.add_subparsers(dest="ttl_cmd")

    base = argparse.ArgumentParser(add_help=False)
    base.add_argument("--vault", required=True)
    base.add_argument("--password", required=True)

    p_set = sub.add_parser("set", parents=[base], help="Set TTL for a key")
    p_set.add_argument("key")
    p_set.add_argument("seconds", type=int)
    p_set.set_defaults(func=cmd_ttl_set)

    p_get = sub.add_parser("get", parents=[base], help="Get TTL for a key")
    p_get.add_argument("key")
    p_get.set_defaults(func=cmd_ttl_get)

    p_clear = sub.add_parser("clear", parents=[base], help="Clear TTL for a key")
    p_clear.add_argument("key")
    p_clear.set_defaults(func=cmd_ttl_clear)

    p_list = sub.add_parser("list", parents=[base], help="List all TTLs")
    p_list.set_defaults(func=cmd_ttl_list)

    p_purge = sub.add_parser("purge", parents=[base], help="Purge expired keys")
    p_purge.set_defaults(func=cmd_ttl_purge)

    return parser


def _ttl_command_handler(args) -> None:
    if not hasattr(args, "func"):
        print("Use a subcommand: set, get, clear, list, purge", file=sys.stderr)
        sys.exit(1)
    args.func(args)


def main():
    parser = build_ttl_parser()
    args = parser.parse_args()
    _ttl_command_handler(args)


if __name__ == "__main__":
    main()
