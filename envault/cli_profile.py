"""CLI commands for environment profile management."""

import argparse
import sys
from envault.vault import Vault, VaultError
from envault.env_profile import (
    ProfileError,
    define_profile,
    delete_profile,
    list_profiles,
    get_profile_keys,
    apply_profile,
)


def _open_vault(args) -> Vault:
    try:
        return Vault(args.vault, password=args.password)
    except VaultError as e:
        print(f"Error opening vault: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_profile_define(args) -> None:
    vault = _open_vault(args)
    try:
        keys = [k.strip() for k in args.keys.split(",") if k.strip()]
        define_profile(vault.path, args.name, keys)
        print(f"Profile '{args.name}' defined with {len(keys)} key(s).")
    except ProfileError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_profile_delete(args) -> None:
    vault = _open_vault(args)
    try:
        delete_profile(vault.path, args.name)
        print(f"Profile '{args.name}' deleted.")
    except ProfileError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_profile_list(args) -> None:
    vault = _open_vault(args)
    profiles = list_profiles(vault.path)
    if not profiles:
        print("No profiles defined.")
    else:
        for name in profiles:
            keys = get_profile_keys(vault.path, name)
            print(f"  {name}: {', '.join(keys)}")


def cmd_profile_apply(args) -> None:
    vault = _open_vault(args)
    try:
        result = apply_profile(vault.path, args.name, vault)
        if not result:
            print(f"No matching keys found for profile '{args.name}'.")
        else:
            for key, value in result.items():
                print(f"{key}={value}")
    except ProfileError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def build_profile_parser(subparsers=None) -> argparse.ArgumentParser:
    if subparsers is None:
        parser = argparse.ArgumentParser(description="Manage environment profiles")
        sub = parser.add_subparsers(dest="subcommand")
    else:
        parser = subparsers.add_parser("profile", help="Manage environment profiles")
        sub = parser.add_subparsers(dest="subcommand")

    for p in [parser]:
        p.add_argument("--vault", required=True)
        p.add_argument("--password", required=True)

    define_p = sub.add_parser("define", help="Define a new profile")
    define_p.add_argument("name")
    define_p.add_argument("--keys", required=True, help="Comma-separated key names")
    define_p.set_defaults(func=cmd_profile_define)

    delete_p = sub.add_parser("delete", help="Delete a profile")
    delete_p.add_argument("name")
    delete_p.set_defaults(func=cmd_profile_delete)

    list_p = sub.add_parser("list", help="List all profiles")
    list_p.set_defaults(func=cmd_profile_list)

    apply_p = sub.add_parser("apply", help="Apply a profile and print key=value pairs")
    apply_p.add_argument("name")
    apply_p.set_defaults(func=cmd_profile_apply)

    return parser


def _profile_command_handler(args) -> None:
    if not hasattr(args, "func"):
        print("No subcommand given. Use --help.", file=sys.stderr)
        sys.exit(1)
    args.func(args)
