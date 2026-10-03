"""API Key Management and Secure Cryptographic Hashing for RETRACE.

Provides secure key generation, SHA-256 hash storage, prefix masking,
and constant-time verification. Plaintext keys are never stored.
"""

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from packages.auth.models import ApiKey, Role

API_KEY_PREFIX = "rt_live_"


def hash_secret(secret: str) -> str:
    """Compute deterministic SHA-256 digest of secret token."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()


def generate_api_key(
    workspace_id: uuid.UUID,
    name: str = "Default API Key",
    role: Role = Role.ANALYST,
    expires_in_days: int | None = None,
) -> tuple[str, ApiKey]:
    """Generate a new secure API key.

    Returns:
        tuple[str, ApiKey]: (plaintext_key_shown_once, api_key_entity_with_hash)
    """
    raw_token = secrets.token_urlsafe(32)
    plaintext_key = f"{API_KEY_PREFIX}{raw_token}"
    hashed = hash_secret(plaintext_key)

    expires_at = (
        datetime.now(UTC) + timedelta(days=expires_in_days)
        if expires_in_days is not None
        else None
    )

    key_record = ApiKey(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        name=name,
        key_prefix=API_KEY_PREFIX,
        hashed_key=hashed,
        role=role,
        created_at=datetime.now(UTC),
        expires_at=expires_at,
    )

    return plaintext_key, key_record


def verify_api_key_secret(plaintext_key: str, hashed_key: str) -> bool:
    """Constant-time verification of plaintext API key against stored SHA-256 hash."""
    computed = hash_secret(plaintext_key)
    return hmac.compare_digest(computed, hashed_key)
