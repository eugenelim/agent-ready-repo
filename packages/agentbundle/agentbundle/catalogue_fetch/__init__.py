"""Catalogue fetch session facade.

Provides ``open_fetch_session`` — a context manager that resolves HTTP access
once via ``credbroker.resolve_http_access`` and binds the result to a
``FetchSession``.  The session exposes bounded byte and file fetch operations
that send credentials only to the bound origin and reject cross-origin or
scheme-downgrade redirects before any request reaches the redirect target.

Bearer, exact-machine ``.netrc``, and anonymous access are supported.  A
JFrog CLI result raises ``CatalogueFetchError`` naming the provider class;
that provider lands in a later task.
"""

from __future__ import annotations

import contextlib
import urllib.request
from collections.abc import Generator, Mapping
from pathlib import Path

from credbroker import (
    AnonymousHttpAccess,
    BearerHttpAccess,
    HttpAccessError,
    JfrogCliHttpAccess,
    NetrcHttpAccess,
    resolve_http_access,
)

from agentbundle.catalogue_fetch import direct_http as _dh
from agentbundle.catalogue_fetch.models import CatalogueFetchError


class FetchSession:
    """A provider-bound fetch session.

    Holds the resolved HTTP access result and an opener configured for the
    bound origin.  Use ``open_fetch_session`` to create a ``FetchSession``
    inside a ``with`` block.

    Attributes:
        provider: Provider literal from the resolved access result
            (e.g. ``"bearer"``, ``"anonymous"``).
        target_origin: Normalized HTTPS origin the session is bound to
            (e.g. ``"https://catalogue.example.test"``).
    """

    def __init__(
        self,
        access: BearerHttpAccess | NetrcHttpAccess | AnonymousHttpAccess,
        opener: urllib.request.OpenerDirector,
    ) -> None:
        self._access = access
        self._opener = opener
        self._bound_origin: str = access.origin
        self._authorization: str | None = (
            access.authorization
            if isinstance(access, (BearerHttpAccess, NetrcHttpAccess))
            else None
        )

    @property
    def provider(self) -> str:
        """Provider literal for the resolved access result."""
        return self._access.provider

    @property
    def target_origin(self) -> str:
        """Normalized HTTPS origin the session is bound to."""
        return self._access.origin

    def fetch_bytes(self, url: str, *, max_bytes: int, timeout: int) -> bytes:
        """Fetch a bounded payload from *url* and return the raw bytes.

        Authorization is sent only when the request URL's normalized origin
        matches the bound origin.  Raises ``CatalogueFetchError`` with code
        ``"descriptor_too_large"`` when the response exceeds *max_bytes*.

        Args:
            url: Target URL (must be on or below the bound origin).
            max_bytes: Hard cap on response bytes.
            timeout: Socket-inactivity timeout in seconds.

        Returns:
            The full response body as bytes.

        Raises:
            CatalogueFetchError: The response exceeds *max_bytes*, or the
                fetch fails for any other reason.
        """
        return _dh.fetch_bytes_bounded(
            self._opener,
            url,
            self._bound_origin,
            self._authorization,
            max_bytes,
            timeout,
        )

    def fetch_archive(self, url: str, *, max_bytes: int, timeout: int) -> Path:
        """Fetch a bounded archive from *url* to a caller-owned temp file.

        The partial temp file is removed on every failure before the exception
        propagates.  Raises ``CatalogueFetchError`` with code
        ``"archive_too_large"`` when the response exceeds *max_bytes*.

        Args:
            url: Target URL (must be on or below the bound origin).
            max_bytes: Hard cap on archive bytes.
            timeout: Socket-inactivity timeout in seconds.

        Returns:
            ``Path`` of the temporary file.  The caller is responsible for
            cleanup on success.

        Raises:
            CatalogueFetchError: The response exceeds *max_bytes*, or the
                fetch fails for any other reason.
        """
        return _dh.stream_to_tempfile(
            self._opener,
            url,
            self._bound_origin,
            self._authorization,
            max_bytes,
            timeout,
        )

    def __enter__(self) -> FetchSession:
        return self

    def __exit__(self, *args: object) -> None:
        pass


@contextlib.contextmanager
def open_fetch_session(
    initial_url: str, *, env: Mapping[str, str]
) -> Generator[FetchSession, None, None]:
    """Resolve access once and yield a bound ``FetchSession``.

    Calls ``credbroker.resolve_http_access(initial_url, env=env)`` exactly
    once.  Bearer and anonymous results produce a session; ``.netrc`` and
    JFrog CLI results are rejected with ``CatalogueFetchError`` (not yet
    supported).  ``HttpAccessError`` from credbroker is wrapped in
    ``CatalogueFetchError`` with a message containing only the provider class
    and code.

    Args:
        initial_url: The initial HTTPS URL (catalogue channel URL or archive
            URL with any ``#sha256=`` fragment already removed).
        env: Environment mapping passed to credbroker for credential
            resolution.  Never reads ``os.environ`` directly.

    Yields:
        A ``FetchSession`` bound to the resolved origin.

    Raises:
        CatalogueFetchError: Access resolution fails, or the resolved provider
            is not yet supported.
    """
    try:
        access = resolve_http_access(initial_url, env=env)
    except HttpAccessError as exc:
        raise CatalogueFetchError(
            f"catalogue access resolution failed: "
            f"provider={exc.provider} code={exc.code}",
            code=None,
        ) from exc

    # JFrog CLI delegation is not yet supported; reject it until its fetch
    # provider lands.
    if isinstance(access, JfrogCliHttpAccess):
        raise CatalogueFetchError(
            f"access provider {type(access).__name__!r} is not yet supported",
            code=None,
        )

    # Build the opener for the resolved origin.
    authorization: str | None = (
        access.authorization
        if isinstance(access, (BearerHttpAccess, NetrcHttpAccess))
        else None
    )
    bound_origin: str = access.origin
    opener = _dh._build_direct_opener(authorization, bound_origin, env=env)
    session = FetchSession(access=access, opener=opener)
    yield session


__all__ = ["FetchSession", "open_fetch_session"]
