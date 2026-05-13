"""CLI commands for vault status reporting."""

import argparse
import sys

from envault.vault import Vault, VaultError
from envault.env_status import get_vault_status, StatusError


def _open_vault(path: str, password: str) -> Vault:
    try:
        return Vault(path, password=password)
    except VaultError as exc:
        print(f"[error] Could not open vault: {exc}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"[error] Vault file not found: {path}", file=sys.stderr)
        sys.exit(1)


def cmd_status(args: argparse.Namespace) -> None:
    vault = _open_vault(args.vault, args.password)
    try:
        status = get_vault_status(vault)
    except StatusError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)

    print(status.summary())

    if args.verbose:
        print()
        if not status.key_statuses:
            print("  (no keys)")
        else:
            for ks in sorted(status.key_statuses, key=lambda k: k.key):
                flags = []
                if ks.pinned:
                    flags.append("pinned")
                if ks.expired:
                    flags.append("EXPIRED")
                flag_str = f"  [{', '.join(flags)}]" if flags else ""
                print(f"  {ks.key}{flag_str}")


def build_status_parser(subparsers=None) -> argparse.ArgumentParser:
    if subparsers is not None:
        parser = subparsers.add_parser("status", help="Show vault status summary")
    else:
        parser = argparse.ArgumentParser(description="Show vault status summary")

    parser.add_argument("--vault", required=True, help="Path to vault file")
    parser.add_argument("--password", required=True, help="Vault password")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show per-key details"
    )
    return parser


def _status_command_handler(args: argparse.Namespace) -> None:
    cmd_status(args)


def main() -> None:
    parser = build_status_parser()
    args = parser.parse_args()
    _status_command_handler(args)


if __name__ == "__main__":
    main()
