"""Integration helper: register diff commands into the main CLI parser."""

from __future__ import annotations
import argparse
from envault.cli_diff import build_diff_parser


def register_diff_commands(subparsers: argparse._SubParsersAction) -> None:
    """Attach all diff-related subcommands to the provided subparsers group."""
    build_diff_parser(subparsers)


def make_diff_cli() -> argparse.ArgumentParser:
    """Build a standalone argument parser for the diff feature (useful for testing)."""
    parser = argparse.ArgumentParser(
        prog="envault-diff",
        description="Compare secrets between two envault vault files.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")
    register_diff_commands(subparsers)
    return parser


if __name__ == "__main__":  # pragma: no cover
    import sys
    cli = make_diff_cli()
    args = cli.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        cli.print_help()
        sys.exit(1)
