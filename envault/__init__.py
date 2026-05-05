"""envault — Lightweight .env secret manager with encryption and team-sharing support."""

from .crypto import encrypt, decrypt

__version__ = "0.1.0"
__all__ = ["encrypt", "decrypt"]
