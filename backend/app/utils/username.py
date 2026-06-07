"""Username and default password generation utilities."""
from __future__ import annotations

import secrets
import unicodedata
from datetime import date


def _normalize(text: str) -> str:
    """Remove accents and keep only ASCII letters, lowercased."""
    normalized = unicodedata.normalize("NFD", text)
    ascii_bytes = normalized.encode("ascii", "ignore")
    return ascii_bytes.decode("ascii").lower()


def generate_username(first_name: str, last_name: str) -> str:
    """Generate a username: first 4 chars of last_name + first 4 chars of first_name.

    Accents are stripped via unicodedata. Result is lowercase ASCII.
    """
    clean_last = _normalize(last_name)
    clean_first = _normalize(first_name)
    return (clean_last[:4] + clean_first[:4])


def ensure_unique_username(base: str, existing_usernames: set[str]) -> str:
    """Return base if not taken, otherwise append 01..99 until unique."""
    if base not in existing_usernames:
        return base
    for i in range(1, 100):
        candidate = f"{base}{i:02d}"
        if candidate not in existing_usernames:
            return candidate
    # Fallback: append random suffix (extremely unlikely to be needed)
    return f"{base}{secrets.token_hex(2)}"


def generate_default_password(username: str, birth_date: date | None) -> str:
    """Generate default password: username + DDMMYYYY if birth_date, else random."""
    if birth_date is not None:
        return username + birth_date.strftime("%d%m%Y")
    return secrets.token_urlsafe(12)
