"""Signing implementation kept behind the public codec."""

import hashlib
import hmac


def sign(body: str, key: bytes) -> str:
    """Return a SHA-256 HMAC."""

    return hmac.new(key, body.encode(), hashlib.sha256).hexdigest()


def verify(body: str, signature: str, key: bytes) -> None:
    """Raise when a signature does not match."""

    if not hmac.compare_digest(sign(body, key), signature):
        raise ValueError("invalid signature")
