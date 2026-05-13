"""CLI commands for secret dependency management."""
from __future__ import annotations

import argparse
import sys

from envault.vault import Vault, VaultError
from envault.env_dependencies import (
    DependencyError,
    add_dependency,
    remove_dependency,
    get_dependencies,
    get_dependents,
    list_all_dependencies,
)


def _open_vault(args: argparse.Namespace) -> Vault:
    try:
        return Vault(args.vault, password=args.password)
    except VaultError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"error: vault not found: {args.vault}", file=sys.stderr)
        sys.exit(1)


def cmd_dep_add(args: argparse.Namespace) -> None:
    vault = _open_vault(args)
    try:
        add_dependency(vault, args.key, args.depends_on)
        print(f"dependency added: '{args.key}' -> '{args.depends_on}'")
    except DependencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_dep_remove(args: argparse.Namespace) -> None:
    vault = _open_vault(args)
    try:
        remove_dependency(vault, args.key, args.depends_on)
        print(f"dependency removed: '{args.key}' -> '{args.depends_on}'")
    except DependencyError as exc:
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_dep_list(args: argparse.Namespace) -> None:
    vault = _open_vault(args)
    deps = get_dependencies(vault, args.key)
    if not deps:
        print(f"no dependencies for '{args.key}'")
    else:
        print(f"'{args.key}' depends on:")
        for d in deps:
            print(f"  - {d}")


def cmd_dep_dependents(args: argparse.Namespace) -> None:
    vault = _open_vault(args)
    dependents = get_dependents(vault, args.key)
    if not dependents:
        print(f"no keys depend on '{args.key}'")
    else:
        print(f"keys that depend on '{args.key}':")
        for k in dependents:
            print(f"  - {k}")


def cmd_dep_all(args: argparse.Namespace) -> None:
    vault = _open_vault(args)
    all_deps = list_all_dependencies(vault)
    if not all_deps:
        print("no dependencies defined")
    else:
        for key, deps in sorted(all_deps.items()):
            print(f"{key}: {', '.join(deps)}")


def build_dep_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("dep", help="manage secret dependencies")
    p.add_argument("--vault", required=True)
    p.add_argument("--password", required=True)
    sub = p.add_subparsers(dest="dep_cmd", required=True)

    add_p = sub.add_parser("add", help="add a dependency")
    add_p.add_argument("key")
    add_p.add_argument("depends_on")
    add_p.set_defaults(func=cmd_dep_add)

    rm_p = sub.add_parser("remove", help="remove a dependency")
    rm_p.add_argument("key")
    rm_p.add_argument("depends_on")
    rm_p.set_defaults(func=cmd_dep_remove)

    ls_p = sub.add_parser("list", help="list dependencies of a key")
    ls_p.add_argument("key")
    ls_p.set_defaults(func=cmd_dep_list)

    rev_p = sub.add_parser("dependents", help="list keys that depend on a key")
    rev_p.add_argument("key")
    rev_p.set_defaults(func=cmd_dep_dependents)

    all_p = sub.add_parser("all", help="list all dependencies")
    all_p.set_defaults(func=cmd_dep_all)
