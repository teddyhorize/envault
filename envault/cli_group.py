"""CLI commands for group management in envault."""

from __future__ import annotations

import argparse
import sys
from typing import Optional

from envault.vault import Vault, VaultError
from envault.env_group import (
    GroupError,
    define_group,
    delete_group,
    list_groups,
    get_group,
    resolve_group,
)


def _open_vault(path: str, password: str) -> Vault:
    try:
        return Vault(path, password=password)
    except VaultError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_group_define(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    keys = args.keys
    try:
        define_group(vault, args.name, keys)
        print(f"[ok] Group '{args.name}' defined with keys: {', '.join(keys)}")
    except GroupError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_group_delete(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        delete_group(vault, args.name)
        print(f"[ok] Group '{args.name}' deleted.")
    except GroupError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)


def cmd_group_list(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    groups = list_groups(vault)
    if not groups:
        print("No groups defined.")
        return
    for name, keys in groups.items():
        print(f"{name}: {', '.join(keys)}")


def cmd_group_show(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        values = resolve_group(vault, args.name)
        for key, value in values.items():
            print(f"{key}={value}")
    except GroupError as e:
        print(f"[error] {e}", file=sys.stderr)
        sys.exit(1)


def build_group_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("group", help="Manage secret groups")
    sp = p.add_subparsers(dest="group_cmd", required=True)

    def _common(sub):
        sub.add_argument("--vault", required=True)
        sub.add_argument("--password", required=True)
        return sub

    define_p = _common(sp.add_parser("define", help="Define a group"))
    define_p.add_argument("name")
    define_p.add_argument("keys", nargs="+")
    define_p.set_defaults(func=cmd_group_define)

    delete_p = _common(sp.add_parser("delete", help="Delete a group"))
    delete_p.add_argument("name")
    delete_p.set_defaults(func=cmd_group_delete)

    list_p = _common(sp.add_parser("list", help="List all groups"))
    list_p.set_defaults(func=cmd_group_list)

    show_p = _common(sp.add_parser("show", help="Show resolved values for a group"))
    show_p.add_argument("name")
    show_p.set_defaults(func=cmd_group_show)


def _group_command_handler(args: argparse.Namespace) -> None:
    args.func(args)
