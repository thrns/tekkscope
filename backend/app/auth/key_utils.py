"""API-key generation and safe presentation helpers."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import uuid


API_KEY_PREFIX = "ts_"


def generate_api_key() -> str:
    """Generate a key compatible with the existing ``ts_<uuid>`` format."""

    return f"{API_KEY_PREFIX}{uuid.uuid4().hex}"


def _peppered_key(key: str) -> bytes:
    pepper = os.getenv("TEKK_API_KEY_PEPPER", "")
    return f"{pepper}:{key}".encode()


def hash_api_key(key: str) -> str:
    return hashlib.sha256(_peppered_key(key)).hexdigest()


def verify_api_key(key: str, expected_hash: str | None) -> bool:
    if not expected_hash:
        return False
    return hmac.compare_digest(hash_api_key(key), expected_hash)


def mask_api_key(key: str | None) -> str | None:
    if not key:
        return None
    visible = key[:10]
    return f"{visible}...{key[-4:]}"


def key_prefix(key: str) -> str:
    return key[:10]


def generate_pepper() -> str:
    """Generate a suggested pepper for local setup documentation."""

    return secrets.token_urlsafe(32)
