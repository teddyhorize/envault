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
    """Entry point for the standalone env-file CLI.

    Parses *argv* (or ``sys.argv[1:]`` when *argv* is ``None``), dispatches to
    the appropriate subcommand handler, and exits with a non-zero status code if
    an unhandled exception is raised during execution.
    """
    parser = make_env_file_cli()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(1)
    try:
        args.func(args)
    except Exception as exc:  # noqa: BLE001
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":  # pragma: no cover
    main()
