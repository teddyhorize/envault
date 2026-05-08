"""CLI commands for secret aliasing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envault.vault import Vault, VaultError
from envault.env_alias import AliasError, add_alias, remove_alias, resolve_alias, list_aliases


def _open_vault(path: str, password: str) -> Vault:
    try:
        return Vault(path, password=password)
    except VaultError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"[error] Vault file not found: {path}", file=sys.stderr)
        sys.exit(1)


def cmd_alias_add(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        add_alias(vault, args.alias, args.target)
        print(f"Alias '{args.alias}' -> '{args.target}' created.")
    except AliasError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_alias_remove(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        remove_alias(vault, args.alias)
        print(f"Alias '{args.alias}' removed.")
    except AliasError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_alias_resolve(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    value = resolve_alias(vault, args.alias)
    if value is None:
        print(f"[error] Alias '{args.alias}' not found or target missing.", file=sys.stderr)
        sys.exit(1)
    print(value)


def cmd_alias_list(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    aliases = list_aliases(vault)
    if not aliases:
        print("No aliases defined.")
        return
    for alias, target in sorted(aliases.items()):
        print(f"  {alias} -> {target}")


def build_alias_parser(subparsers=None) -> argparse.ArgumentParser:
    if subparsers is None:
        parser = argparse.ArgumentParser(description="Manage secret aliases")
        sub = parser.add_subparsers(dest="alias_cmd")
    else:
        parser = subparsers.add_parser("alias", help="Manage secret aliases")
        sub = parser.add_subparsers(dest="alias_cmd")

    for sp in (parser,):
        sp  # noqa: keep reference

    add_p = sub.add_parser("add", help="Add an alias")
    add_p.add_argument("alias")
    add_p.add_argument("target", help="Existing vault key to alias")
    add_p.set_defaults(func=cmd_alias_add)

    rm_p = sub.add_parser("remove", help="Remove an alias")
    rm_p.add_argument("alias")
    rm_p.set_defaults(func=cmd_alias_remove)

    res_p = sub.add_parser("resolve", help="Resolve alias to its value")
    res_p.add_argument("alias")
    res_p.set_defaults(func=cmd_alias_resolve)

    list_p = sub.add_parser("list", help="List all aliases")
    list_p.set_defaults(func=cmd_alias_list)

    return parser


def _alias_command_handler(args: argparse.Namespace) -> None:
    if not hasattr(args, "func"):
        print("Usage: envault alias <add|remove|resolve|list>", file=sys.stderr)
        sys.exit(1)
    args.func(args)
