"""CLI commands for vault linting."""

from __future__ import annotations

import argparse
import sys

from envault.vault import Vault, VaultError
from envault.lint import lint_vault, LintError


def _open_vault(vault_path: str, password: str) -> Vault:
    try:
        return Vault(vault_path, password)
    except VaultError as exc:
        print(f"Error opening vault: {exc}", file=sys.stderr)
        sys.exit(1)


def cmd_lint(args: argparse.Namespace) -> None:
    """Run lint checks on the vault and report issues."""
    vault = _open_vault(args.vault, args.password)

    try:
        result = lint_vault(vault, args.password)
    except LintError as exc:
        print(f"Lint error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not result.has_issues:
        print("✔ No issues found.")
        return

    if result.errors:
        print(f"Errors ({len(result.errors)}):")
        for issue in result.errors:
            print(f"  [ERROR]   {issue.key}: {issue.message}")

    if result.warnings:
        print(f"Warnings ({len(result.warnings)}):")
        for issue in result.warnings:
            print(f"  [WARNING] {issue.key}: {issue.message}")

    print()
    print(result.summary())

    if result.errors and not args.no_fail:
        sys.exit(2)


def build_lint_parser(subparsers=None) -> argparse.ArgumentParser:
    description = "Lint vault secrets for common issues."
    if subparsers is not None:
        parser = subparsers.add_parser("lint", help=description)
    else:
        parser = argparse.ArgumentParser(prog="envault-lint", description=description)

    parser.add_argument("--vault", required=True, help="Path to the vault file.")
    parser.add_argument("--password", required=True, help="Vault password.")
    parser.add_argument(
        "--no-fail",
        action="store_true",
        default=False,
        help="Exit with code 0 even when errors are found.",
    )
    parser.set_defaults(func=cmd_lint)
    return parser


def _lint_command_handler(args: argparse.Namespace) -> None:
    cmd_lint(args)


def main() -> None:
    parser = build_lint_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
