"""CLI commands for tag management."""

from __future__ import annotations

import argparse
import sys
from typing import List

from envault.vault import Vault, VaultError
from envault.tags import TagsError, add_tag, remove_tag, get_tags, keys_by_tag, all_tags


def _open_vault(path: str, password: str) -> Vault:
    try:
        return Vault(path, password=password)
    except VaultError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_tag_add(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        add_tag(vault, args.key, args.tag)
        print(f"Tag '{args.tag}' added to '{args.key}'.")
    except TagsError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_tag_remove(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        removed = remove_tag(vault, args.key, args.tag)
        if removed:
            print(f"Tag '{args.tag}' removed from '{args.key}'.")
        else:
            print(f"Tag '{args.tag}' was not present on '{args.key}'.")
    except TagsError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_tag_list(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        if args.key:
            tags = get_tags(vault, args.key)
            if tags:
                print(f"Tags for '{args.key}': {', '.join(tags)}")
            else:
                print(f"No tags for '{args.key}'.")
        else:
            mapping = all_tags(vault)
            if not mapping:
                print("No tags defined.")
            else:
                for key, tags in sorted(mapping.items()):
                    print(f"  {key}: {', '.join(tags)}")
    except TagsError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_tag_filter(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    keys = keys_by_tag(vault, args.tag)
    if keys:
        for k in sorted(keys):
            print(k)
    else:
        print(f"No secrets found with tag '{args.tag}'.")


def build_tags_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    p = subparsers.add_parser("tags", help="Manage secret tags")
    p.add_argument("--vault", required=True, help="Path to vault file")
    p.add_argument("--password", required=True, help="Vault password")
    sub = p.add_subparsers(dest="tags_cmd", required=True)

    pa = sub.add_parser("add", help="Add a tag to a secret")
    pa.add_argument("key"); pa.add_argument("tag")
    pa.set_defaults(func=cmd_tag_add)

    pr = sub.add_parser("remove", help="Remove a tag from a secret")
    pr.add_argument("key"); pr.add_argument("tag")
    pr.set_defaults(func=cmd_tag_remove)

    pl = sub.add_parser("list", help="List tags")
    pl.add_argument("key", nargs="?", default=None)
    pl.set_defaults(func=cmd_tag_list)

    pf = sub.add_parser("filter", help="List secrets by tag")
    pf.add_argument("tag")
    pf.set_defaults(func=cmd_tag_filter)


def _tags_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
