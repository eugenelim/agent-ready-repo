"""Direct HTTPS fetch provider for bearer and anonymous catalogue access.

Implements the HTTP mechanics for ``FetchSession`` on the direct (non-JFrog)
path.  All host comparisons use ``credbroker.resolve_http_access`` for origin
normalization, which applies ASCII-lowercase then stdlib IDNA encoding — the
same profile Python uses when opening the TCP connection.  This gives byte
identity between the compared origin, the bound origin, and the connected host.

Authorization is attached only to requests whose normalized origin matches the
bound origin.  Same-origin HTTPS redirects forward Authorization; cross-origin
and scheme-downgrade redirects are rejected *before* any request is sent to the
redirect target.
"""

from __future__ import annotations

import contextlib
import os
import ssl
import tempfile
import urllib.error
import urllib.request
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

from credbroker import HttpAccessError, resolve_http_access

from agentbundle.catalogue_fetch.models import CatalogueFetchError

# Read chunk size — 64 KiB, matches the original https_catalogue constant.
_CHUNK = 65536


def _normalize_origin(url: str) -> str:
    """Return the normalized HTTPS origin for *url* using credbroker's codec.

    Calls ``resolve_http_access(url, env={})`` (empty env → anonymous, no I/O)
    and returns the resulting ``AnonymousHttpAccess.origin`` string, which is
    normalized under the single host-normalization profile: ASCII-lowercase then
    stdlib IDNA encoding.

    Raises ``CatalogueFetchError`` if *url* is not a valid HTTPS target.
    """
    try:
        result = resolve_http_access(url, env={})
    except HttpAccessError:
        raise CatalogueFetchError(
            "URL is not a valid HTTPS target",
            code=None,
        ) from None
    # Every non-jfrog result has an ``origin`` attribute; jfrog is never reached
    # with env={} because the provider is unavailable without a PATH entry.
    origin: str = result.origin  # type: ignore[union-attr]
    return origin


def _normalized_url(url: str, bound_origin: str) -> tuple[str, str]:
    """Return ``(normalized_url, request_origin)`` for *url*.

    The URL's host is replaced with the IDNA-normalized form so the connected
    host is byte-identical to the bound origin.  The fragment is removed
    (fragments are never sent to the server).

    Raises ``CatalogueFetchError`` when *url* is not a valid HTTPS target.
    """
    request_origin = _normalize_origin(url)
    parsed = urlsplit(url)
    # Replace netloc with the origin host (without scheme, no fragment).
    norm_host = request_origin[len("https://"):]  # e.g. "host" or "host:port"
    norm_url = urlunsplit(parsed._replace(netloc=norm_host, fragment=""))
    return norm_url, request_origin


class _DirectHttpRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler enforcing same-origin policy with credbroker normalization.

    Cross-origin and scheme-downgrade redirects are rejected *inside*
    ``redirect_request`` before the redirected request is sent.  Same-origin
    HTTPS redirects are allowed and the ``Authorization`` header is forwarded.
    """

    def __init__(self, bound_origin: str, authorization: str | None) -> None:
        self._bound_origin = bound_origin
        self._authorization = authorization

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        parsed = urlsplit(newurl)

        # Reject scheme downgrade.
        if parsed.scheme.lower() != "https":
            raise CatalogueFetchError(
                f"HTTPS-only: redirect to non-HTTPS URL rejected: {parsed.scheme}://...",
                code="redirect_not_permitted",
            )
        # Reject user-info in redirect URL.
        if "@" in parsed.netloc:
            raise CatalogueFetchError(
                "redirect contains user-info in netloc; rejected",
                code="redirect_not_permitted",
            )

        # Normalize redirect URL's origin and compare with bound origin.
        try:
            redirect_origin = _normalize_origin(newurl)
        except CatalogueFetchError:
            raise CatalogueFetchError(
                "redirect target is not a valid HTTPS origin; rejected",
                code="redirect_not_permitted",
            ) from None

        if redirect_origin != self._bound_origin:
            raise CatalogueFetchError(
                "cross-origin redirect rejected",
                code="redirect_not_permitted",
            )

        # Same-origin HTTPS redirect: allow and forward Authorization.
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is not None and self._authorization:
            # add_unredirected_header avoids urllib stripping it on 302 GET.
            new_req.add_unredirected_header("Authorization", self._authorization)
        return new_req


def _build_direct_opener(
    authorization: str | None,
    bound_origin: str,
    *,
    env: Mapping[str, str],
) -> urllib.request.OpenerDirector:
    """Build an HTTPS-only opener with proxy, redirect enforcement, and CA support.

    - ``ProxyHandler()`` (no args) reads proxy settings from ``os.environ``
      automatically via ``urllib.request.getproxies()``.
    - No ``HTTPHandler`` — only HTTPS is allowed.
    - ``_DirectHttpRedirectHandler`` rejects cross-origin and scheme-downgrade
      redirects before the redirected request is sent.
    - ``AGENTBUNDLE_CA_BUNDLE`` from the supplied ``env`` mapping overrides the
      default trust store.
    - ``addheaders`` is cleared so no ``User-Agent`` leaks by default.

    Args:
        authorization: Full ``Authorization`` header value (e.g. ``"Bearer
            <token>"``), or ``None`` for anonymous access.
        bound_origin: Normalized HTTPS origin the session is bound to.
        env: Environment mapping consulted for ``AGENTBUNDLE_CA_BUNDLE``.

    Returns:
        A configured ``OpenerDirector`` ready to open HTTPS URLs.

    Raises:
        CatalogueFetchError: ``AGENTBUNDLE_CA_BUNDLE`` is set but the path
            does not exist.
    """
    redirect_handler = _DirectHttpRedirectHandler(bound_origin, authorization)
    proxy_handler = urllib.request.ProxyHandler()

    ca_bundle = env.get("AGENTBUNDLE_CA_BUNDLE")
    if ca_bundle:
        if not Path(ca_bundle).exists():
            raise CatalogueFetchError(
                f"AGENTBUNDLE_CA_BUNDLE path does not exist: {ca_bundle!r}",
                code=None,
            )
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        ctx.load_verify_locations(cafile=ca_bundle)
        https_handler = urllib.request.HTTPSHandler(context=ctx)
    else:
        https_handler = urllib.request.HTTPSHandler()

    opener = urllib.request.OpenerDirector()
    opener.addheaders = []

    opener.add_handler(proxy_handler)
    opener.add_handler(redirect_handler)
    opener.add_handler(https_handler)
    opener.add_handler(urllib.request.UnknownHandler())

    return opener


def _make_direct_request(
    url: str,
    bound_origin: str,
    authorization: str | None,
) -> urllib.request.Request:
    """Build a ``Request`` with a normalized URL, adding ``Authorization`` to the bound origin.

    The URL's host is replaced with its IDNA-normalized form (byte identity
    with the bound origin).  The ``Authorization`` header is attached only when
    the request URL's normalized origin equals the bound origin.

    Raises:
        CatalogueFetchError: The URL is not a valid HTTPS target.
    """
    norm_url, req_origin = _normalized_url(url, bound_origin)
    req = urllib.request.Request(norm_url)
    if authorization and req_origin == bound_origin:
        req.add_header("Authorization", authorization)
    return req


def fetch_bytes_bounded(
    opener: urllib.request.OpenerDirector,
    url: str,
    bound_origin: str,
    authorization: str | None,
    max_bytes: int,
    timeout: int,
) -> bytes:
    """Stream a response and enforce ``max_bytes`` regardless of Content-Length.

    Raises:
        CatalogueFetchError: The response exceeds ``max_bytes``
            (code ``"descriptor_too_large"``), or the fetch fails.
    """
    req = _make_direct_request(url, bound_origin, authorization)
    try:
        with opener.open(req, timeout=timeout) as resp:
            chunks = []
            total = 0
            while True:
                chunk = resp.read(_CHUNK)
                if not chunk:
                    break
                total += len(chunk)
                if total > max_bytes:
                    raise CatalogueFetchError(
                        f"response exceeds {max_bytes} byte limit",
                        code="descriptor_too_large",
                    )
                chunks.append(chunk)
            return b"".join(chunks)
    except CatalogueFetchError:
        raise
    except urllib.error.URLError as exc:
        raise CatalogueFetchError(
            f"failed to fetch: {exc.reason}",
            code=None,
        ) from exc
    except OSError as exc:
        raise CatalogueFetchError(
            f"failed to fetch: {exc}",
            code=None,
        ) from exc


def stream_to_tempfile(
    opener: urllib.request.OpenerDirector,
    url: str,
    bound_origin: str,
    authorization: str | None,
    max_bytes: int,
    timeout: int,
) -> Path:
    """Stream *url* to a temporary file, enforcing ``max_bytes``.

    Returns the ``Path`` of the temp file on success; the caller owns the file
    and is responsible for cleanup.  On any failure the partial temp file is
    removed before the exception propagates.

    Raises:
        CatalogueFetchError: The response exceeds ``max_bytes``
            (code ``"archive_too_large"``), or the fetch fails.
    """
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        prefix="agentbundle-archive-", suffix=".tar.gz"
    )
    tmp_path = Path(tmp_path_str)
    try:
        req = _make_direct_request(url, bound_origin, authorization)
        total = 0
        try:
            with opener.open(req, timeout=timeout) as resp, os.fdopen(tmp_fd, "wb") as tmp_file:
                tmp_fd = -1  # fd now owned by tmp_file
                while True:
                    chunk = resp.read(_CHUNK)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > max_bytes:
                        raise CatalogueFetchError(
                            f"archive exceeds {max_bytes} byte limit",
                            code="archive_too_large",
                        )
                    tmp_file.write(chunk)
        except CatalogueFetchError:
            raise
        except urllib.error.URLError as exc:
            raise CatalogueFetchError(
                f"failed to fetch archive: {exc.reason}",
                code=None,
            ) from exc
        except OSError as exc:
            raise CatalogueFetchError(
                f"failed to fetch archive: {exc}",
                code=None,
            ) from exc
        return tmp_path
    except Exception:
        if tmp_fd >= 0:
            with contextlib.suppress(OSError):
                os.close(tmp_fd)
        with contextlib.suppress(OSError):
            tmp_path.unlink(missing_ok=True)
        raise
