"""CLI commands for managing scheduled secret rotations."""

import argparse
import sys
from datetime import datetime

from envault.vault import Vault, VaultError
from envault.env_schedule import (
    ScheduleError,
    schedule_rotation,
    remove_schedule,
    get_schedule,
    list_schedules,
    due_keys,
)


def _open_vault(path: str, password: str) -> Vault:
    try:
        return Vault(path, password=password)
    except VaultError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_schedule_add(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        next_due = schedule_rotation(vault, args.key, args.interval)
        ts = datetime.fromtimestamp(next_due).strftime("%Y-%m-%d %H:%M:%S")
        print(f"Scheduled '{args.key}' for rotation every {args.interval}s. Next due: {ts}")
    except ScheduleError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_schedule_remove(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        remove_schedule(vault, args.key)
        print(f"Removed rotation schedule for '{args.key}'.")
    except ScheduleError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_schedule_list(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    entries = list_schedules(vault)
    if not entries:
        print("No rotation schedules configured.")
        return
    for entry in entries:
        ts = datetime.fromtimestamp(entry["next_due"]).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {entry['key']}: every {entry['interval']}s, next due {ts}")


def cmd_schedule_due(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    keys = due_keys(vault)
    if not keys:
        print("No keys are currently due for rotation.")
    else:
        print("Keys due for rotation:")
        for k in keys:
            print(f"  {k}")


def build_schedule_parser(subparsers=None):
    if subparsers is None:
        parser = argparse.ArgumentParser(prog="envault-schedule")
        sub = parser.add_subparsers(dest="subcommand")
    else:
        parser = subparsers.add_parser("schedule", help="Manage rotation schedules")
        sub = parser.add_subparsers(dest="subcommand")

    for cmd, func, extra in [
        ("add", cmd_schedule_add, [("key",), ("interval", int)]),
        ("remove", cmd_schedule_remove, [("key",)]),
        ("list", cmd_schedule_list, []),
        ("due", cmd_schedule_due, []),
    ]:
        p = sub.add_parser(cmd)
        p.add_argument("--vault", required=True)
        p.add_argument("--password", required=True)
        for item in extra:
            if len(item) == 2:
                p.add_argument(item[0], type=item[1])
            else:
                p.add_argument(item[0])
        p.set_defaults(func=func)

    return parser


def _schedule_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("Use a subcommand: add, remove, list, due", file=sys.stderr)
        sys.exit(1)
