"""CLI commands for secret rotation in envault."""

import argparse
import sys
from envault.vault import Vault, VaultError
from envault.rotation import RotationError, rotate_secret


def cmd_rotate(
    vault_path: str,
    vault_password: str,
    key: str,
    new_value: str,
    show_old: bool = False,
) -> None:
    """Rotate a single secret in the vault.

    Args:
        vault_path: Path to the vault file.
        vault_password: Password to unlock the vault.
        key: The secret key to rotate.
        new_value: The replacement plaintext value.
        show_old: If True, print the previous value to stdout.
    """
    try:
        vault = Vault(vault_path, password=vault_password)
    except VaultError as exc:
        print(f"[envault] vault error: {exc}", file=sys.stderr)
        sys.exit(1)

    try:
        old_value = rotate_secret(vault, key, new_value)
    except RotationError as exc:
        print(f"[envault] rotation error: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"[envault] rotated '{key}' successfully.")
    if show_old:
        print(f"[envault] previous value: {old_value}")


def build_rotation_parser(subparsers: argparse._SubParsersAction) -> None:
    """Register the 'rotate' sub-command on an existing subparsers object."""
    parser = subparsers.add_parser(
        "rotate",
        help="Rotate (replace) the value of an existing secret.",
    )
    parser.add_argument("key", help="Secret key to rotate.")
    parser.add_argument("new_value", help="New plaintext value for the secret.")
    parser.add_argument(
        "--show-old",
        action="store_true",
        default=False,
        help="Print the previous secret value after rotation.",
    )
    parser.set_defaults(func=_rotation_command_handler)


def _rotation_command_handler(args: argparse.Namespace) -> None:
    """Dispatch handler invoked by the CLI framework."""
    cmd_rotate(
        vault_path=args.vault,
        vault_password=args.password,
        key=args.key,
        new_value=args.new_value,
        show_old=args.show_old,
    )
