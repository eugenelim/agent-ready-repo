"""Fetch-error model for the catalogue fetch session.

Defines ``CatalogueFetchError`` — the single error type raised by every
bounded-fetch path.  It subclasses ``CatalogueError`` so all existing
callers that catch ``CatalogueError`` remain compatible.

The ``code`` attribute carries a stable, non-secret failure code from a
closed set.  The code is *not* interpolated into the message.
"""

from __future__ import annotations

from agentbundle.catalogue import CatalogueError

# Closed code set for AgentBundle-side fetch failures.
VALID_FETCH_CODES: frozenset[str] = frozenset(
    {
        "jfrog_fetch_stderr_too_large",
        "descriptor_too_large",
        "archive_too_large",
        "jfrog_fetch_timeout",
        "jfrog_fetch_failed",
        "redirect_not_permitted",
        "endpoint_not_permitted",
    }
)


class CatalogueFetchError(CatalogueError):
    """Terminal error raised by catalogue fetch operations.

    Subclasses ``CatalogueError`` so callers that catch the base class
    still work.  Carries a stable non-secret ``code`` attribute (``None``
    when no code applies, e.g. for provider-rejection errors).

    The ``code`` is never interpolated into the message text so it can be
    inspected programmatically without parsing.

    Attributes:
        code: A stable failure code from ``VALID_FETCH_CODES``, or ``None``.
    """

    def __init__(self, message: str, *, code: str | None = None) -> None:
        if code is not None and code not in VALID_FETCH_CODES:
            raise ValueError(
                f"Unknown CatalogueFetchError code: {code!r}; "
                f"must be one of the VALID_FETCH_CODES set"
            )
        super().__init__(message)
        self.code: str | None = code
