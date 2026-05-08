"""CLI commands for vault watch feature."""
from __future__ import annotations

import argparse
import signal
import sys
import time
from typing import Optional

from envault.vault import Vault, VaultError
from envault.env_watch import VaultWatcher, WatchError, WatchEvent


def _open_vault(vault_path: str, password: str) -> Vault:
    try:
        return Vault(vault_path, password=password)
    except VaultError as exc:
        print(f"[envault] Error opening vault: {exc}", file=sys.stderr)
        sys.exit(1)


def _on_change(event: WatchEvent) -> None:
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(event.new_mtime))
    print(f"[{ts}] Vault changed: {event.vault_path}")


def cmd_watch(args: argparse.Namespace) -> None:
    """Watch a vault file and print a message whenever it changes."""
    vault = _open_vault(args.vault, args.password)
    try:
        watcher = VaultWatcher(vault, interval=args.interval)
    except WatchError as exc:
        print(f"[envault] Watch error: {exc}", file=sys.stderr)
        sys.exit(1)

    watcher.on_change(_on_change)
    watcher.start()
    print(f"[envault] Watching {vault.path} (interval={args.interval}s). Press Ctrl+C to stop.")

    def _handle_signal(sig, frame):  # noqa: ANN001
        watcher.stop()
        print("\n[envault] Watch stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    while watcher.is_running():
        time.sleep(0.5)


def build_watch_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("watch", help="Watch vault for external changes")
    parser.add_argument("vault", help="Path to the vault file")
    parser.add_argument("--password", required=True, help="Vault password")
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds (default: 2.0)",
    )
    parser.set_defaults(func=cmd_watch)


def _watch_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("[envault] No watch sub-command specified.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="envault watch commands")
    subparsers = parser.add_subparsers()
    build_watch_parser(subparsers)
    args = parser.parse_args()
    _watch_command_handler(args)


if __name__ == "__main__":
    main()
