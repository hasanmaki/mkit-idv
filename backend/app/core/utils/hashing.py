"""Password hashing utilities."""

from __future__ import annotations

from functools import lru_cache

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher


@lru_cache
def get_password_hasher() -> PasswordHash:
    """Return a singleton PasswordHash using Argon2."""
    return PasswordHash([Argon2Hasher()])


def hash_password(password: str) -> str:
    """Hash a plain password."""
    return get_password_hasher().hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash."""
    return get_password_hasher().verify(password, hashed_password)
