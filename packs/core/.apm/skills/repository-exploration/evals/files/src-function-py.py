"""Auth session module."""

from __future__ import annotations

import hashlib
import hmac


class AuthResult:
    """Authentication attempt outcome."""

    def __init__(self, success: bool, user_id: str | None = None) -> None:
        self.success = success
        self.user_id = user_id

    def __bool__(self) -> bool:
        return self.success


MAX_SESSION_HOURS = 8


def authenticate(credentials: dict) -> AuthResult:
    """Validate credentials and return an AuthResult."""
    if not credentials.get("user_id"):
        return AuthResult(success=False)
    expected = hmac.new(
        b"session-secret",
        repr(sorted(credentials.items())).encode(),
        hashlib.sha256,
    ).hexdigest()
    supplied = credentials.get("token", "")
    if not hmac.compare_digest(expected, supplied):
        return AuthResult(success=False)
    return AuthResult(success=True, user_id=credentials["user_id"])
