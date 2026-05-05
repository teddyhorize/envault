"""Minimal CLI for envault vault operations."""

import getpass
import sys

from envault.vault import Vault, VaultError

USAGE = """
Usage: envault <command> [args]

Commands:
  set   <key> <value>   Store an encrypted secret
  get   <key>           Retrieve a secret
  del   <key>           Delete a secret
  list                  List all secret keys
  export                Print secrets as KEY=VALUE lines
""".strip()


def _get_vault(vault_file: str = ".envault") -> Vault:
    password = getpass.getpass("Vault password: ")
    return Vault(path=vault_file, password=password)


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    if not argv:
        print(USAGE)
        return 0

    command, *args = argv

    try:
        if command == "set":
            if len(args) != 2:
                print("Usage: envault set <key> <value>", file=sys.stderr)
                return 1
            vault = _get_vault()
            vault.set(args[0], args[1])
            print(f"✓ Secret '{args[0]}' saved.")

        elif command == "get":
            if len(args) != 1:
                print("Usage: envault get <key>", file=sys.stderr)
                return 1
            vault = _get_vault()
            value = vault.get(args[0])
            if value is None:
                print(f"Key '{args[0]}' not found.", file=sys.stderr)
                return 1
            print(value)

        elif command == "del":
            if len(args) != 1:
                print("Usage: envault del <key>", file=sys.stderr)
                return 1
            vault = _get_vault()
            removed = vault.delete(args[0])
            if removed:
                print(f"✓ Secret '{args[0]}' deleted.")
            else:
                print(f"Key '{args[0]}' not found.", file=sys.stderr)
                return 1

        elif command == "list":
            vault = _get_vault()
            keys = vault.list_keys()
            if keys:
                print("\n".join(keys))
            else:
                print("(vault is empty)")

        elif command == "export":
            vault = _get_vault()
            print(vault.export_env())

        else:
            print(f"Unknown command: {command}\n", file=sys.stderr)
            print(USAGE)
            return 1

    except VaultError as exc:
        print(f"Vault error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nAborted.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
