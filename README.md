# envault

> Lightweight .env secret manager with encryption and team-sharing support

---

## Installation

```bash
pip install envault
```

---

## Usage

Initialize a vault in your project directory:

```bash
envault init
```

Add and encrypt a secret:

```bash
envault set DATABASE_URL "postgres://user:pass@localhost/db"
```

Load secrets into your environment:

```bash
envault run -- python app.py
```

Share secrets with your team by exporting an encrypted bundle:

```bash
envault export --out secrets.vault
envault import secrets.vault
```

Access secrets directly in Python:

```python
import envault

envault.load()  # decrypts and injects secrets into os.environ

import os
print(os.getenv("DATABASE_URL"))
```

---

## How It Works

- Secrets are encrypted using **AES-256** before being stored in `.vault` files
- A shared team key (stored separately) is used to decrypt secrets across environments
- `.vault` files are safe to commit to version control — your raw secrets never are

---

## License

[MIT](LICENSE) © envault contributors