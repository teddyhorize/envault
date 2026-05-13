"""CLI commands for secret strength checking."""

import argparse
import sys

from envault.vault import Vault, VaultError
from envault.env_secret_strength import StrengthError, check_strength, check_all_strengths


def _open_vault(path: str, password: str) -> Vault:
    try:
        return Vault(path, password)
    except VaultError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)


_SCORE_ICONS = ["\u2716", "\u2716", "\u26a0", "\u2714", "\u2714"]


def _print_result(result) -> None:
    icon = _SCORE_ICONS[result.score]
    print(f"  {icon}  {result.key}: {result.label} (score {result.score}/4)")
    for suggestion in result.suggestions:
        print(f"       - {suggestion}")


def cmd_strength_check(args: argparse.Namespace) -> None:
    """Check strength of a single secret."""
    vault = _open_vault(args.vault, args.password)
    try:
        result = check_strength(vault, args.password, args.key)
    except StrengthError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)
    _print_result(result)


def cmd_strength_all(args: argparse.Namespace) -> None:
    """Check strength of all secrets in the vault."""
    vault = _open_vault(args.vault, args.password)
    try:
        results = check_all_strengths(vault, args.password)
    except StrengthError as exc:
        print(f"[error] {exc}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("Vault is empty.")
        return

    print(f"Strength report for {len(results)} secret(s):")
    for result in results:
        _print_result(result)

    weak = [r for r in results if r.score <= 1]
    if weak:
        print(f"\n[warning] {len(weak)} secret(s) are weak or very weak.")


def build_strength_parser(subparsers) -> None:
    p_check = subparsers.add_parser("check", help="Check strength of a single secret.")
    p_check.add_argument("vault", help="Path to vault file.")
    p_check.add_argument("password", help="Vault password.")
    p_check.add_argument("key", help="Secret key to check.")
    p_check.set_defaults(func=cmd_strength_check)

    p_all = subparsers.add_parser("all", help="Check strength of all secrets.")
    p_all.add_argument("vault", help="Path to vault file.")
    p_all.add_argument("password", help="Vault password.")
    p_all.set_defaults(func=cmd_strength_all)


def _strength_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("Use 'check' or 'all'. See --help.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description="envault secret strength checker")
    subparsers = parser.add_subparsers(dest="command")
    build_strength_parser(subparsers)
    args = parser.parse_args()
    _strength_command_handler(args)


if __name__ == "__main__":
    main()
