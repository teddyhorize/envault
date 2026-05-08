"""Integration helpers: register watch commands into a top-level CLI."""
from __future__ import annotations

import argparse

from envault.cli_watch import build_watch_parser, _watch_command_handler


def register_watch_commands(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Attach the 'watch' sub-command to an existing subparsers group."""
    build_watch_parser(subparsers)


def make_watch_cli() -> argparse.ArgumentParser:
    """Build a standalone argument parser for watch commands."""
    parser = argparse.ArgumentParser(
        prog="envault-watch",
        description="envault: watch vault for external changes",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    register_watch_commands(subparsers)
    return parser


def main() -> None:
    """Entry point for the standalone watch CLI."""
    import sys

    parser = make_watch_cli()
    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    _watch_command_handler(args)


if __name__ == "__main__":
    main()
