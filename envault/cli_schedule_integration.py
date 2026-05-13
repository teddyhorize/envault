"""Integration entry point for the envault schedule CLI."""

import argparse
import sys

from envault.cli_schedule import build_schedule_parser, _schedule_command_handler


def register_schedule_commands(subparsers: argparse.Action) -> None:
    """Attach schedule subcommands to an existing subparsers group."""
    build_schedule_parser(subparsers)


def make_schedule_cli() -> argparse.ArgumentParser:
    """Build and return a standalone schedule CLI parser."""
    parser = argparse.ArgumentParser(
        prog="envault-schedule",
        description="Manage scheduled secret rotations.",
    )
    sub = parser.add_subparsers(dest="subcommand")
    build_schedule_parser(sub)
    parser.set_defaults(func=_schedule_command_handler)
    return parser


def main(argv=None) -> None:
    parser = make_schedule_cli()
    args = parser.parse_args(argv)
    if not args.subcommand:
        parser.print_help()
        sys.exit(1)
    _schedule_command_handler(args)


if __name__ == "__main__":
    main()
