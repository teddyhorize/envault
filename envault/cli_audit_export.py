"""CLI commands for exporting the audit log."""
from __future__ import annotations

import argparse
import sys

from envault.env_audit_export import export_audit_log, AuditExportError


def _open_vault_args(args: argparse.Namespace):
    return args.vault, args.password


def cmd_audit_export(args: argparse.Namespace) -> None:
    """Handle the 'audit-export' sub-command."""
    vault_path, password = _open_vault_args(args)
    fmt = args.format
    output = getattr(args, "output", None)

    try:
        payload = export_audit_log(vault_path, password, fmt=fmt, output_path=output)
    except AuditExportError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if output:
        print(f"Audit log exported to '{output}' ({fmt.upper()} format).")
    else:
        print(payload)


def build_audit_export_parser(
    subparsers: argparse.Action,
) -> argparse.ArgumentParser:
    """Register audit-export sub-command on *subparsers*."""
    parser = subparsers.add_parser(
        "audit-export",
        help="Export the audit log to JSON or CSV.",
    )
    parser.add_argument("vault", help="Path to the vault file.")
    parser.add_argument("password", help="Vault password.")
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout.",
    )
    parser.set_defaults(func=cmd_audit_export)
    return parser


def _audit_export_command_handler(args: argparse.Namespace) -> None:
    if hasattr(args, "func"):
        args.func(args)
    else:
        print("Use 'audit-export --help' for usage.", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="envault-audit-export",
        description="Export envault audit log.",
    )
    subparsers = parser.add_subparsers()
    build_audit_export_parser(subparsers)
    args = parser.parse_args()
    _audit_export_command_handler(args)


if __name__ == "__main__":
    main()
