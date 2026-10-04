"""Catalogue fetch session facade.

Provides ``open_fetch_session`` — a context manager that resolves HTTP access
once via ``credbroker.resolve_http_access`` and binds the result to a
``FetchSession``.  The session exposes bounded byte and file fetch operations
that send credentials only to the bound origin and reject cross-origin or
scheme-downgrade redirects before any request reaches the redirect target.

Bearer, exact-machine ``.netrc``, anonymous, and JFrog CLI access are
supported.  ``HttpAccessError`` from credbroker is wrapped in a
``CatalogueFetchError``; no credential material is included in any
diagnostic message.
"""

from __future__ import annotations

import contextlib
import urllib.request
from collections.abc import Generator, Mapping
from pathlib import Path
from urllib.parse import urlsplit

from credbroker import (
    AnonymousHttpAccess,
    BearerHttpAccess,
    HttpAccessError,
    JfrogCliHttpAccess,
    NetrcHttpAccess,
    resolve_http_access,
)

from agentbundle.catalogue_fetch import direct_http as _dh
from agentbundle.catalogue_fetch import jfrog_cli as _jf
from agentbundle.catalogue_fetch.models import CatalogueFetchError


class FetchSession:
    """A provider-bound fetch session.

    Holds the resolved HTTP access result and, for direct-HTTP providers, an
    opener configured for the bound origin.  For JFrog CLI access the session
    delegates to an internal ``JfrogFetchSession``.  Use
    ``open_fetch_session`` to create a ``FetchSession`` inside a ``with``
    block.

    Attributes:
        provider: Provider literal from the resolved access result
            (``"bearer"``, ``"jfrog"``, ``"netrc"``, or ``"anonymous"``).
        target_origin: Normalized HTTPS origin the session is bound to.
    """

    def __init__(
        self,
        access: BearerHttpAccess | NetrcHttpAccess | AnonymousHttpAccess | JfrogCliHttpAccess,
        opener: urllib.request.OpenerDirector | None,
        *,
        jfrog_session: _jf.JfrogFetchSession | None = None,
    ) -> None:
        self._access = access
        self._opener = opener
        self._jfrog_session = jfrog_session

        if isinstance(access, JfrogCliHttpAccess):
            # Derive the target origin from the pinned Artifactory URL.
            artf_parsed = urlsplit(access.artifactory_url)
            self._bound_origin = f"https://{artf_parsed.netloc}"
            self._authorization: str | None = None
        else:
            self._bound_origin = access.origin
            self._authorization = (
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
        return self._bound_origin

    def fetch_bytes(self, url: str, *, max_bytes: int, timeout: int) -> bytes:
        """Fetch a bounded payload from *url* and return the raw bytes.

        For JFrog access, delegates to the internal ``JfrogFetchSession``.
        For direct-HTTP access, authorization is sent only when the request
        URL's normalized origin matches the bound origin.

        Args:
            url: Target URL (must be on or below the bound origin).
            max_bytes: Hard cap on response bytes.
            timeout: Timeout in seconds (socket-inactivity for direct HTTP;
                subprocess deadline for JFrog).

        Returns:
            The full response body as bytes.

        Raises:
            CatalogueFetchError: The response exceeds *max_bytes*, or the
                fetch fails for any other reason.
        """
        if self._jfrog_session is not None:
            # A delegated call may be shortened by the caller but never runs
            # past the per-call bound, which keeps the aggregate budget fixed.
            return self._jfrog_session.fetch_bytes(
                url, max_bytes=max_bytes, timeout=min(timeout, _jf._JFROG_FETCH_TIMEOUT)
            )
        assert self._opener is not None
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
        propagates.

        For JFrog access, the returned file is at most ``max_bytes`` bytes.
        When the JFrog CLI appends one trailing ``0x0a`` byte, the digest-
        checked trim in ``catalogue_fetch/jfrog_cli.py`` truncates the file to
        ``max_bytes`` before returning it.

        Args:
            url: Target URL (must be on or below the bound origin).
            max_bytes: Hard cap on archive bytes.
            timeout: Timeout in seconds.

        Returns:
            ``Path`` of the temporary file.  The caller is responsible for
            cleanup on success.

        Raises:
            CatalogueFetchError: The response exceeds *max_bytes*, or the
                fetch fails for any other reason.
        """
        if self._jfrog_session is not None:
            # A delegated call may be shortened by the caller but never runs
            # past the per-call bound, which keeps the aggregate budget fixed.
            return self._jfrog_session.fetch_archive(
                url, max_bytes=max_bytes, timeout=min(timeout, _jf._JFROG_FETCH_TIMEOUT)
            )
        assert self._opener is not None
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
    once.  All four provider results (bearer, JFrog CLI, .netrc, anonymous)
    produce a session.  ``HttpAccessError`` from credbroker is wrapped in
    ``CatalogueFetchError`` with a message containing only the provider class
    and code — no credential material.

    Args:
        initial_url: The initial HTTPS URL (catalogue channel URL or archive
            URL with any ``#sha256=`` fragment already removed).
        env: Environment mapping passed to credbroker for credential
            resolution.  Never reads ``os.environ`` directly.

    Yields:
        A ``FetchSession`` bound to the resolved origin.

    Raises:
        CatalogueFetchError: Access resolution fails for any configured-but-
            broken condition.
    """
    try:
        access = resolve_http_access(initial_url, env=env)
    except HttpAccessError as exc:
        raise CatalogueFetchError(
            f"catalogue access resolution failed: "
            f"provider={exc.provider} code={exc.code}",
            code=None,
        ) from exc

    if isinstance(access, JfrogCliHttpAccess):
        # JFrog CLI path: delegate fetches to a bounded subprocess session.
        jfrog_session = _jf.JfrogFetchSession(access, env)
        session = FetchSession(access=access, opener=None, jfrog_session=jfrog_session)
        yield session
        return

    # Direct-HTTP path: bearer, .netrc, or anonymous.
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
