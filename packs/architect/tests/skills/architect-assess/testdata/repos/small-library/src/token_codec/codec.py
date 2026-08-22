"""Versioned token encoding."""

from .signing import sign, verify


def encode(payload: str, key: bytes) -> str:
    """Encode a versioned payload."""

    body = f"v1:{payload}"
    return f"{body}:{sign(body, key)}"


def decode(token: str, key: bytes) -> str:
    """Verify and decode a versioned payload."""

    body, signature = token.rsplit(":", 1)
    verify(body, signature, key)
    version, payload = body.split(":", 1)
    if version != "v1":
        raise ValueError("unsupported version")
    return payload
