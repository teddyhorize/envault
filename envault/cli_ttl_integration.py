"""Integration helpers: register TTL commands into a top-level CLI."""

import argparse
import sys

from envault.cli_ttl import build_ttl_parser, _ttl_command_handler


def register_ttl_commands(subparsers: argparse.Action) -> None:
    """Attach the 'ttl' subcommand group to an existing subparsers object."""
    ttl_parser = subparsers.add_parser(
        "ttl",
        help="Manage per-secret time-to-live (TTL) settings",
    )
    sub = ttl_parser.add_subparsers(dest="ttl_cmd")
    build_ttl_parser(sub)
    ttl_parser.set_defaults(func=_ttl_command_handler)


def make_ttl_cli() -> argparse.ArgumentParser:
    """Return a standalone ArgumentParser for TTL commands."""
    parser = argparse.ArgumentParser(
        prog="envault-ttl",
        description="Manage secret TTLs in an envault vault",
    )
    sub = parser.add_subparsers(dest="ttl_cmd")
    build_ttl_parser(sub)
    parser.set_defaults(func=_ttl_command_handler)
    return parser


def main() -> None:
    parser = make_ttl_cli()
    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
