"""Integration entry point for group CLI commands."""

from __future__ import annotations

import argparse
import sys

from envault.cli_group import build_group_parser, _group_command_handler


def register_group_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register group subcommands onto an existing subparsers object."""
    build_group_parser(subparsers)


def make_group_cli() -> argparse.ArgumentParser:
    """Create a standalone argument parser for group commands."""
    parser = argparse.ArgumentParser(
        prog="envault-group",
        description="Manage named groups of secrets in envault.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    build_group_parser(subparsers)
    return parser


def main(argv=None) -> None:
    parser = make_group_cli()
    args = parser.parse_args(argv)
    _group_command_handler(args)


if __name__ == "__main__":
    main()
