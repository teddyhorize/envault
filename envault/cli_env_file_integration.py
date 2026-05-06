"""Integration helpers: register .env import/export commands into a top-level CLI."""
from __future__ import annotations

import argparse
import sys

from envault.cli_env_file import build_env_file_parser


def register_env_file_commands(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach import-env and export-env subcommands to *subparsers*."""
    build_env_file_parser(subparsers)


def make_env_file_cli() -> argparse.ArgumentParser:
    """Return a standalone ArgumentParser with import-env / export-env commands.

    Useful for testing or running the env-file feature in isolation.
    """
    parser = argparse.ArgumentParser(
        prog="envault-env",
        description="Import/export vault secrets to/from .env files",
    )
    subparsers = parser.add_subparsers(dest="command")
    build_env_file_parser(subparsers)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = make_env_file_cli()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":  # pragma: no cover
    main()
