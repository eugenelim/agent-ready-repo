"""Pure locator minimization for delivery-brief source provenance."""

from __future__ import annotations

import re
from urllib.parse import urlsplit, urlunsplit


class SourceAdmissionError(ValueError):
    """Stable refusal raised before any effect."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


_EMAIL_RE = re.compile(r"\b[^\s/@]+@[^\s/@]+\.[^\s/@]+\b")
_SECRET_RE = re.compile(
    r"(?i)(?:^|[/;])(?:password|passwd|pwd|secret|api[_-]?key|"
    r"access[_-]?token|token)(?:[:=]|/)[^/?#]+"
)
_PERSONAL_ABSOLUTE_RE = re.compile(
    r"(?i)^(?:/(?:users|home|private)/|[a-z]:[/\\]users[/\\])"
)
_ABSOLUTE_LOCAL_RE = re.compile(r"(?i)^(?:/|[a-z]:[/\\]|\\\\)")


def minimize_source_locator(locator: str) -> str:
    """Strip non-identity URL data without touching the named resource."""

    if not isinstance(locator, str) or not locator or any(
        character in locator for character in ("\x00", "\r", "\n")
    ):
        raise SourceAdmissionError("unsafe_source_locator")
    if _PERSONAL_ABSOLUTE_RE.match(locator):
        raise SourceAdmissionError("personal_source_locator")
    if _is_unsafe_local_locator(locator):
        raise SourceAdmissionError("unsafe_source_locator")
    try:
        parsed = urlsplit(locator)
    except ValueError as error:
        raise SourceAdmissionError("unsafe_source_locator") from error

    if parsed.scheme:
        if parsed.scheme.lower() == "file" or not parsed.hostname:
            raise SourceAdmissionError("unsafe_source_locator")
        if parsed.path in {"", "/"} and (parsed.query or parsed.fragment):
            raise SourceAdmissionError("source_identity_lost")
        try:
            port = parsed.port
        except ValueError as error:
            raise SourceAdmissionError("unsafe_source_locator") from error
        host = parsed.hostname
        if ":" in host and not host.startswith("["):
            host = f"[{host}]"
        netloc = f"{host}:{port}" if port is not None else host
        minimized = urlunsplit(
            (parsed.scheme.lower(), netloc, parsed.path or "/", "", "")
        )
    else:
        minimized = locator.split("?", 1)[0].split("#", 1)[0]

    minimized = minimized.strip()
    if not minimized or minimized in {"/", "."}:
        raise SourceAdmissionError("source_identity_lost")
    if _EMAIL_RE.search(minimized) or _SECRET_RE.search(minimized):
        raise SourceAdmissionError("sensitive_source_locator")
    if _PERSONAL_ABSOLUTE_RE.match(minimized):
        raise SourceAdmissionError("personal_source_locator")
    return minimized


def _is_unsafe_local_locator(value: str) -> bool:
    """Reject local path shapes lexically without touching the filesystem."""

    return bool(_ABSOLUTE_LOCAL_RE.match(value)) or "\\" in value or any(
        part in {".", ".."} for part in value.split("/")
    )
