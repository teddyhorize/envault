"""CLI commands for searching vault secrets."""

from __future__ import annotations

import argparse
import sys
from typing import Dict

from envault.vault import Vault, VaultError
from envault.search import SearchError, search_by_pattern, search_by_tag


def _open_vault(path: str, password: str) -> Vault:
    try:
        return Vault(path, password)
    except VaultError as exc:
        print(f"[error] Could not open vault: {exc}", file=sys.stderr)
        sys.exit(1)


def _print_results(results: Dict[str, str]) -> None:
    if not results:
        print("No matching secrets found.")
        return
    for key, value in sorted(results.items()):
        print(f"  {key}={value}")


def cmd_search_pattern(args: argparse.Namespace) -> None:
    """Search secrets by glob pattern."""
    vault = _open_vault(args.vault, args.password)
    try:
        results = search_by_pattern(vault, args.pattern, args.password)
    except SearchError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)
    _print_results(results)


def cmd_search_tag(args: argparse.Namespace) -> None:
    """Search secrets by tag."""
    vault = _open_vault(args.vault, args.password)
    try:
        results = search_by_tag(vault, args.tag, args.password)
    except SearchError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)
    _print_results(results)


def build_search_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    search_parser = subparsers.add_parser("search", help="Search secrets in the vault")
    search_sub = search_parser.add_subparsers(dest="search_cmd", required=True)

    # pattern sub-command
    p_pattern = search_sub.add_parser("pattern", help="Search by key glob pattern")
    p_pattern.add_argument("pattern", help="Glob pattern, e.g. DB_*")
    p_pattern.add_argument("--vault", required=True, help="Path to vault file")
    p_pattern.add_argument("--password", required=True, help="Vault password")
    p_pattern.set_defaults(func=cmd_search_pattern)

    # tag sub-command
    p_tag = search_sub.add_parser("tag", help="Search by tag")
    p_tag.add_argument("tag", help="Tag name to filter by")
    p_tag.add_argument("--vault", required=True, help="Path to vault file")
    p_tag.add_argument("--password", required=True, help="Vault password")
    p_tag.set_defaults(func=cmd_search_tag)


def _search_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("Use 'search pattern' or 'search tag'.", file=sys.stderr)
        sys.exit(1)
