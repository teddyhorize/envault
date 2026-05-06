"""CLI commands for access control management."""
from __future__ import annotations

import argparse
import sys

from envault.access_control import (
    AccessControlError,
    grant_access,
    revoke_access,
    get_roles,
    list_access,
)


def _open_vault(args: argparse.Namespace) -> str:
    return args.vault


def cmd_grant(args: argparse.Namespace) -> None:
    vault_path = _open_vault(args)
    try:
        grant_access(vault_path, args.user, args.role)
        print(f"Granted role '{args.role}' to user '{args.user}'.")
    except AccessControlError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_revoke(args: argparse.Namespace) -> None:
    vault_path = _open_vault(args)
    role = getattr(args, "role", None)
    try:
        revoke_access(vault_path, args.user, role)
        if role:
            print(f"Revoked role '{role}' from user '{args.user}'.")
        else:
            print(f"Revoked all roles from user '{args.user}'.")
    except AccessControlError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_list_access(args: argparse.Namespace) -> None:
    vault_path = _open_vault(args)
    acl = list_access(vault_path)
    if not acl:
        print("No access entries found.")
        return
    for user, roles in sorted(acl.items()):
        print(f"{user}: {', '.join(sorted(roles))}")


def cmd_show_roles(args: argparse.Namespace) -> None:
    vault_path = _open_vault(args)
    roles = get_roles(vault_path, args.user)
    if not roles:
        print(f"User '{args.user}' has no roles assigned.")
    else:
        print(f"{args.user}: {', '.join(sorted(roles))}")


def build_access_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("access", help="Manage vault access control")
    p.add_argument("--vault", required=True, help="Path to vault file")
    sub = p.add_subparsers(dest="access_cmd", required=True)

    g = sub.add_parser("grant", help="Grant a role to a user")
    g.add_argument("user", help="Username")
    g.add_argument("role", help="Role to grant (reader/writer/admin)")
    g.set_defaults(func=cmd_grant)

    r = sub.add_parser("revoke", help="Revoke a role (or all) from a user")
    r.add_argument("user", help="Username")
    r.add_argument("role", nargs="?", default=None, help="Role to revoke (omit for all)")
    r.set_defaults(func=cmd_revoke)

    ls = sub.add_parser("list", help="List all access entries")
    ls.set_defaults(func=cmd_list_access)

    sh = sub.add_parser("show", help="Show roles for a specific user")
    sh.add_argument("user", help="Username")
    sh.set_defaults(func=cmd_show_roles)


def _access_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("No access subcommand provided.", file=sys.stderr)
        sys.exit(1)
