"""CLI commands for vault locking."""

import argparse
import sys
from envault.env_lock import acquire_lock, release_lock, is_locked, get_lock_info


def cmd_lock(args: argparse.Namespace) -> None:
    """Acquire a lock on the vault."""
    if is_locked(args.vault):
        info = get_lock_info(args.vault)
        owner = info.get("owner", "unknown") if info else "unknown"
        print(f"[error] Vault is already locked by '{owner}'.", file=sys.stderr)
        sys.exit(1)

    owner = args.owner or "envault"
    acquired = acquire_lock(args.vault, owner=owner)
    if acquired:
        print(f"Vault locked by '{owner}'.")
    else:
        print("[error] Failed to acquire lock.", file=sys.stderr)
        sys.exit(1)


def cmd_unlock(args: argparse.Namespace) -> None:
    """Release the lock on the vault."""
    if not is_locked(args.vault):
        print("Vault is not locked.")
        return
    release_lock(args.vault)
    print("Vault unlocked.")


def cmd_lock_status(args: argparse.Namespace) -> None:
    """Show current lock status of the vault."""
    if not is_locked(args.vault):
        print("Vault is unlocked.")
        return
    info = get_lock_info(args.vault)
    if info:
        import datetime
        ts = datetime.datetime.fromtimestamp(info["acquired_at"]).isoformat()
        print(f"Vault is LOCKED")
        print(f"  Owner  : {info.get('owner', 'unknown')}")
        print(f"  PID    : {info.get('pid', 'unknown')}")
        print(f"  Since  : {ts}")
    else:
        print("Vault is LOCKED (no metadata available).")


def build_lock_parser(subparsers):
    p_lock = subparsers.add_parser("lock", help="Lock the vault")
    p_lock.add_argument("vault", help="Path to the vault file")
    p_lock.add_argument("--owner", default=None, help="Lock owner identifier")
    p_lock.set_defaults(func=cmd_lock)

    p_unlock = subparsers.add_parser("unlock", help="Unlock the vault")
    p_unlock.add_argument("vault", help="Path to the vault file")
    p_unlock.set_defaults(func=cmd_unlock)

    p_status = subparsers.add_parser("lock-status", help="Show vault lock status")
    p_status.add_argument("vault", help="Path to the vault file")
    p_status.set_defaults(func=cmd_lock_status)


def _lock_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("[error] No lock subcommand specified.", file=sys.stderr)
        sys.exit(1)
