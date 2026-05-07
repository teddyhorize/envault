"""Integration entry point for profile CLI commands."""

import argparse
import sys
from envault.cli_profile import build_profile_parser, _profile_command_handler


def register_profile_commands(subparsers) -> None:
    """Register profile subcommands onto an existing subparsers object."""
    profile_parser = subparsers.add_parser(
        "profile",
        help="Manage environment profiles (dev, staging, prod, etc.)",
    )
    profile_parser.add_argument("--vault", required=True, help="Path to vault file")
    profile_parser.add_argument("--password", required=True, help="Vault password")

    sub = profile_parser.add_subparsers(dest="subcommand")

    define_p = sub.add_parser("define", help="Define a named profile")
    define_p.add_argument("name", help="Profile name")
    define_p.add_argument("--keys", required=True, help="Comma-separated key names")

    delete_p = sub.add_parser("delete", help="Delete a named profile")
    delete_p.add_argument("name", help="Profile name")

    sub.add_parser("list", help="List all defined profiles")

    apply_p = sub.add_parser("apply", help="Print key=value pairs for a profile")
    apply_p.add_argument("name", help="Profile name")

    profile_parser.set_defaults(func=_profile_command_handler)


def make_profile_cli() -> argparse.ArgumentParser:
    """Build a standalone CLI parser for profile commands."""
    return build_profile_parser()


def main() -> None:
    parser = make_profile_cli()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
