"""Integration helpers to register history commands into a top-level CLI."""
from __future__ import annotations

import argparse
import sys

from envault.cli_history import build_history_parser, _history_command_handler


def register_history_commands(subparsers: argparse._SubParsersAction) -> None:
    """Attach the 'history' sub-command tree to an existing subparsers group."""
    history_parser = build_history_parser(subparsers)
    history_parser.set_defaults(func=_history_command_handler)


def make_history_cli() -> argparse.ArgumentParser:
    """Return a standalone argument parser for the history feature."""
    parser = argparse.ArgumentParser(
        prog="envault-history",
        description="Manage secret version history in an envault vault.",
    )
    sub = parser.add_subparsers(dest="history_cmd")
    build_history_parser(sub)
    return parser


def main(argv=None) -> None:
    parser = make_history_cli()
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
