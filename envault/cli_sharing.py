"""CLI commands for team sharing (export-bundle / import-bundle)."""

import sys
from pathlib import Path

from envault.vault import Vault, VaultError
from envault.sharing import export_bundle, import_bundle, SharingError


def cmd_export_bundle(
    vault_path: str,
    vault_password: str,
    share_password: str,
    output_file: str | None = None,
) -> None:
    """Export vault secrets to an encrypted bundle.

    If *output_file* is given the bundle is written there; otherwise it is
    printed to stdout.
    """
    vault = Vault(Path(vault_path))
    try:
        bundle = export_bundle(vault, vault_password, share_password)
    except (VaultError, SharingError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if output_file:
        Path(output_file).write_text(bundle)
        print(f"Bundle written to {output_file}")
    else:
        print(bundle)


def cmd_import_bundle(
    vault_path: str,
    vault_password: str,
    share_password: str,
    bundle_source: str,
    overwrite: bool = False,
) -> None:
    """Import secrets from a bundle file or inline bundle string.

    *bundle_source* may be a file path (if the file exists) or a raw bundle
    string.
    """
    vault = Vault(Path(vault_path))

    src_path = Path(bundle_source)
    if src_path.exists():
        bundle_str = src_path.read_text().strip()
    else:
        bundle_str = bundle_source.strip()

    try:
        imported = import_bundle(
            bundle_str,
            share_password,
            vault,
            vault_password,
            overwrite=overwrite,
        )
    except (VaultError, SharingError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if imported:
        print(f"Imported {len(imported)} secret(s): {', '.join(imported)}")
    else:
        print("No new secrets imported (all keys already exist; use --overwrite to replace).")
