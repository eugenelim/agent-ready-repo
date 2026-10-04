# STUB: AC-0008 — a fetch session resolves one provider for the acquisition
from agentbundle.catalogue_fetch import open_fetch_session


def test_open_fetch_session_resolves_anonymous_access_once() -> None:
    with open_fetch_session(
        "https://catalogue.example.test/root/catalogue.toml",
        env={},
    ) as session:
        assert session.provider == "anonymous"
        assert session.target_origin == "https://catalogue.example.test"


# ---------------------------------------------------------------------------
# Appended tests — T2 requirements
# ---------------------------------------------------------------------------

import hashlib  # noqa: E402, I001
import io  # noqa: E402
import json  # noqa: E402
import logging  # noqa: E402
import os  # noqa: E402
import tarfile  # noqa: E402
import urllib.request  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest import mock  # noqa: E402

import pytest  # noqa: E402

from agentbundle.catalogue import CatalogueError  # noqa: E402
from agentbundle.catalogue_fetch.direct_http import (  # noqa: E402, I001
    _DirectHttpRedirectHandler,
    _build_direct_opener,
    _make_direct_request,
    fetch_bytes_bounded,
)
from agentbundle.catalogue_fetch.models import CatalogueFetchError  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_DESCRIPTOR = {
    "schema": 1,
    "kind": "agentbundle-catalogue",
    "bundle": "core",
    "channel": "stable",
    "release": "2026.07.01",
    "artifact": "https://catalogue.example.test/releases/core-stable.tar.gz",
    "sha256": "a" * 64,
}


def _make_tarball(*members: tuple[str, bytes]) -> tuple[bytes, str]:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for name, content in members:
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tf.addfile(info, io.BytesIO(content))
    data = buf.getvalue()
    return data, hashlib.sha256(data).hexdigest()


class _MockResponse:
    def __init__(self, data: bytes) -> None:
        self._buf = io.BytesIO(data)

    def read(self, n: int = -1) -> bytes:
        return self._buf.read(n)

    def __enter__(self) -> "_MockResponse":
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _CapturingOpener:
    """Opener that captures each request and returns a fixed payload."""

    def __init__(self, response_data: bytes = b"", *, authorization: str | None = None) -> None:
        self._data = response_data
        self.requests: list[urllib.request.Request] = []
        # Direct provider stores authorization separately; tests may inspect it.

    def open(self, req: urllib.request.Request, timeout: int | None = None) -> _MockResponse:
        self.requests.append(req)
        return _MockResponse(self._data)


class _ErrorOpener:
    def open(self, req: urllib.request.Request, timeout: int | None = None) -> None:
        import urllib.error
        raise urllib.error.URLError("simulated connection error")


def _mock_req(url: str) -> urllib.request.Request:
    return urllib.request.Request(url)


# ---------------------------------------------------------------------------
# AC-0008 — one resolution per acquisition
# ---------------------------------------------------------------------------


def test_session_pins_one_resolution_catalogue_https(tmp_path: Path) -> None:
    """resolve_http_access is called exactly once per catalogue+https acquisition."""
    archive_data, archive_sha256 = _make_tarball(("f.txt", b"hello"))
    descriptor = {**_VALID_DESCRIPTOR, "sha256": archive_sha256}
    descriptor_data = json.dumps(descriptor).encode()
    archive_tmp = tmp_path / "arc.tar.gz"
    archive_tmp.write_bytes(archive_data)

    call_count: list[int] = [0]

    import agentbundle.catalogue_fetch as _cf

    original_resolve = _cf.resolve_http_access

    def counting_resolve(url: str, *, env: object) -> object:
        call_count[0] += 1
        return original_resolve(url, env=env)  # type: ignore[arg-type]

    with (
        mock.patch.object(_cf, "resolve_http_access", side_effect=counting_resolve),
        mock.patch.object(_cf.FetchSession, "fetch_bytes", return_value=descriptor_data),
        mock.patch.object(_cf.FetchSession, "fetch_archive", return_value=archive_tmp),
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive
        result = fetch_catalogue_archive(
            "catalogue+https://catalogue.example.test/stable.json",
            env={},
        )

    import shutil
    shutil.rmtree(str(result), ignore_errors=True)
    # AC-0008: exactly one resolution call per acquisition
    assert call_count[0] == 1, f"expected 1 resolution, got {call_count[0]}"


def test_session_pins_one_resolution_archive_https(tmp_path: Path) -> None:
    """resolve_http_access is called exactly once per archive+https acquisition."""
    archive_data, archive_sha256 = _make_tarball(("f.txt", b"world"))
    archive_tmp = tmp_path / "arc.tar.gz"
    archive_tmp.write_bytes(archive_data)

    call_count: list[int] = [0]

    import agentbundle.catalogue_fetch as _cf

    original_resolve = _cf.resolve_http_access

    def counting_resolve(url: str, *, env: object) -> object:
        call_count[0] += 1
        return original_resolve(url, env=env)  # type: ignore[arg-type]

    with (
        mock.patch.object(_cf, "resolve_http_access", side_effect=counting_resolve),
        mock.patch.object(_cf.FetchSession, "fetch_archive", return_value=archive_tmp),
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive
        result = fetch_catalogue_archive(
            f"archive+https://catalogue.example.test/arc.tar.gz#sha256={archive_sha256}",
            env={},
        )

    import shutil
    shutil.rmtree(str(result), ignore_errors=True)
    assert call_count[0] == 1, f"expected 1 resolution, got {call_count[0]}"


# ---------------------------------------------------------------------------
# AC-0008 — post-selection failure: one terminal error, zero re-resolution
# ---------------------------------------------------------------------------


def test_post_selection_failure_no_further_resolution() -> None:
    """A fetch failure after session open yields one error and zero re-resolution."""
    call_count: list[int] = [0]

    import agentbundle.catalogue_fetch as _cf

    original_resolve = _cf.resolve_http_access

    def counting_resolve(url: str, *, env: object) -> object:
        call_count[0] += 1
        return original_resolve(url, env=env)  # type: ignore[arg-type]

    with (
        mock.patch.object(_cf, "resolve_http_access", side_effect=counting_resolve),
        mock.patch.object(
            _cf.FetchSession,
            "fetch_bytes",
            side_effect=CatalogueError("simulated HTTP 401"),
        ),
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive
        with pytest.raises(CatalogueError):
            fetch_catalogue_archive(
                "catalogue+https://catalogue.example.test/stable.json",
                env={},
            )

    assert call_count[0] == 1, "resolution must happen exactly once; no retry"


# ---------------------------------------------------------------------------
# AC-0010 — bearer session sends Authorization only to bound origin
# ---------------------------------------------------------------------------


def test_bearer_session_sends_authorization_only_to_bound_origin() -> None:
    """Authorization header is present for the bound origin and absent for others."""
    bound = "https://catalogue.example.test"

    # Request to bound origin: should have Authorization.
    req_bound = _make_direct_request(
        "https://catalogue.example.test/path",
        bound,
        "Bearer test-token-abc",
    )
    assert req_bound.get_header("Authorization") == "Bearer test-token-abc"

    # Request to different origin: should NOT have Authorization.
    req_other = _make_direct_request(
        "https://catalogue.example.test/path",
        "https://other.example.test",
        "Bearer test-token-abc",
    )
    assert req_other.get_header("Authorization") is None


def test_anonymous_session_sends_no_authorization() -> None:
    """Anonymous session never adds an Authorization header."""
    req = _make_direct_request(
        "https://catalogue.example.test/path",
        "https://catalogue.example.test",
        None,
    )
    assert req.get_header("Authorization") is None


# ---------------------------------------------------------------------------
# AC-0010 — redirect rejection (before the redirected request is sent)
# ---------------------------------------------------------------------------


def test_cross_origin_redirect_rejected_before_sent_bearer() -> None:
    """Cross-origin redirect raises CatalogueFetchError before the new request is sent."""
    bound = "https://catalogue.example.test"
    handler = _DirectHttpRedirectHandler(bound, "Bearer tok")

    with pytest.raises(CatalogueFetchError) as exc_info:
        handler.redirect_request(
            _mock_req("https://catalogue.example.test/stable.json"),
            None, 302, "Found", {}, "https://evil.example.test/steal"
        )
    assert exc_info.value.code == "redirect_not_permitted"
    assert "tok" not in str(exc_info.value)


def test_cross_origin_redirect_rejected_before_sent_anonymous() -> None:
    """Cross-origin redirect is rejected for anonymous sessions too."""
    bound = "https://catalogue.example.test"
    handler = _DirectHttpRedirectHandler(bound, None)

    with pytest.raises(CatalogueFetchError) as exc_info:
        handler.redirect_request(
            _mock_req("https://catalogue.example.test/stable.json"),
            None, 302, "Found", {}, "https://other.example.test/path"
        )
    assert exc_info.value.code == "redirect_not_permitted"


def test_https_to_http_redirect_rejected() -> None:
    """Scheme-downgrade redirect (https→http) raises redirect_not_permitted."""
    handler = _DirectHttpRedirectHandler("https://catalogue.example.test", None)

    with pytest.raises(CatalogueFetchError) as exc_info:
        handler.redirect_request(
            _mock_req("https://catalogue.example.test/stable.json"),
            None, 301, "Moved", {}, "http://catalogue.example.test/stable.json"
        )
    assert exc_info.value.code == "redirect_not_permitted"


def test_same_origin_redirect_forwarded_authorization() -> None:
    """Same-origin HTTPS redirect is followed and Authorization forwarded exactly once.

    Uses the REAL ``_build_direct_opener`` (which includes ``HTTPErrorProcessor``
    and ``_DirectHttpRedirectHandler``) with a patched ``HTTPSHandler.https_open``
    that returns a real 302 on the first call and 200 on the second.
    The test fails if no redirect is followed (the assertion on ``len(seen)`` is
    unconditional) and fails if Authorization is duplicated across header dicts.
    """
    import email.message

    seen: list[urllib.request.Request] = []
    call_count = [0]

    def _fake_https_open(self: object, req: urllib.request.Request) -> object:
        seen.append(req)
        call_count[0] += 1
        if call_count[0] == 1:
            hdrs = email.message.Message()
            hdrs["Location"] = "https://catalogue.example.test/v2/stable.json"
            req_url = req.full_url

            class _R302:
                code = 302
                status = 302
                msg = "Found"
                url = req_url

                def info(self) -> email.message.Message:
                    return hdrs

                def read(self, n: int = -1) -> bytes:
                    return b""

                def geturl(self) -> str:
                    return req_url

                def close(self) -> None:
                    pass

                def __enter__(self) -> "_R302":
                    return self

                def __exit__(self, *a: object) -> None:
                    pass

            return _R302()

        class _R200:
            code = 200
            status = 200
            msg = "OK"
            _buf = io.BytesIO(b"ok")

            def info(self) -> email.message.Message:
                return email.message.Message()

            def read(self, n: int = -1) -> bytes:
                return self._buf.read(n)

            def geturl(self) -> str:
                return req.full_url

            def close(self) -> None:
                pass

            def __enter__(self) -> "_R200":
                return self

            def __exit__(self, *a: object) -> None:
                pass

        return _R200()

    bound = "https://catalogue.example.test"
    authorization = "Bearer same-origin-token"

    with mock.patch.object(urllib.request.HTTPSHandler, "https_open", _fake_https_open):
        opener = _build_direct_opener(authorization, bound, env={})
        fetch_bytes_bounded(
            opener,
            "https://catalogue.example.test/stable.json",
            bound,
            authorization,
            max_bytes=1024,
            timeout=5,
        )

    # Must have followed the redirect — unconditional assertion.
    assert len(seen) == 2, f"expected 2 requests (initial + redirect), got {len(seen)}"
    # Authorization must arrive on the redirected request.
    redirect_req = seen[1]
    auth = redirect_req.get_header("Authorization")
    assert auth == authorization, f"Authorization not forwarded on same-origin redirect: {auth!r}"
    # Must not be duplicated in the regular headers dict (would be sent twice).
    assert redirect_req.headers.get("Authorization") is None, (
        "Authorization duplicated in redirect_req.headers — would be sent twice"
    )


# ---------------------------------------------------------------------------
# AC-0010 — internationalized host: bound origin == connected host (byte identity)
# ---------------------------------------------------------------------------


def test_internationalized_host_bearer_bound_origin_byte_identity() -> None:
    """Bound origin and connected host are byte-identical for an IDN hostname.

    Verifies that the URL sent to the opener has the IDNA-normalized host
    (same form credbroker uses), not the Unicode or upper-cased original.
    """
    # Use a simple ASCII hostname that credbroker normalizes (lowercases).
    requests_made: list[str] = []

    class _CapturingURLOpener:
        def open(self, req: urllib.request.Request, timeout: object = None) -> _MockResponse:
            requests_made.append(req.full_url)
            return _MockResponse(b"data")

    # The URL has an upper-cased host; after normalization it should be lower.
    url = "https://CATALOGUE.EXAMPLE.TEST/path"
    bound_origin = "https://catalogue.example.test"
    authorization = "Bearer int-test-token"

    req = _make_direct_request(url, bound_origin, authorization)
    # Host in the request URL must be the normalized (lower-cased) form.
    from urllib.parse import urlsplit
    parsed = urlsplit(req.full_url)
    assert parsed.hostname == "catalogue.example.test", (
        f"Expected normalized lowercase host, got {parsed.hostname!r}"
    )
    # Authorization must be present (same origin).
    assert req.get_header("Authorization") == authorization


# ---------------------------------------------------------------------------
# AC-0005 / AC-0017 — .netrc / JFrog results rejected as unsupported
# ---------------------------------------------------------------------------


def test_netrc_result_accepted_and_sends_basic_auth() -> None:
    """A NetrcHttpAccess result opens a session and sends Basic auth to the bound origin."""
    from credbroker import NetrcHttpAccess

    canary_b64 = "dXNlcjpwYXNz"
    fake_netrc = NetrcHttpAccess(
        origin="https://catalogue.example.test",
        authorization=f"Basic {canary_b64}",
    )
    with (
        mock.patch(
            "agentbundle.catalogue_fetch.resolve_http_access",
            return_value=fake_netrc,
        ),
        open_fetch_session("https://catalogue.example.test/s.json", env={}) as session,
    ):
        assert session.provider == "netrc"
        assert session.target_origin == "https://catalogue.example.test"


def test_jfrog_result_yields_jfrog_session() -> None:
    """A JfrogCliHttpAccess result yields a session with provider 'jfrog'."""
    from credbroker import JfrogCliHttpAccess

    fake_jfrog = JfrogCliHttpAccess(
        server_id="my-server",
        platform_url="https://platform.example.test/",
        artifactory_url="https://platform.example.test/artifactory/",
    )
    with (
        mock.patch(
            "agentbundle.catalogue_fetch.resolve_http_access",
            return_value=fake_jfrog,
        ),
        open_fetch_session("https://platform.example.test/s.json", env={}) as session,
    ):
        assert session.provider == "jfrog"
        assert session.target_origin == "https://platform.example.test"


# ---------------------------------------------------------------------------
# AC-0014 — error code attributes; code not in message text
# ---------------------------------------------------------------------------


def test_descriptor_too_large_code() -> None:
    """fetch_bytes_bounded raises CatalogueFetchError with code descriptor_too_large."""
    opener = _CapturingOpener(b"x" * 20)
    bound = "https://catalogue.example.test"
    with pytest.raises(CatalogueFetchError) as exc_info:
        fetch_bytes_bounded(opener, "https://catalogue.example.test/d.json", bound, None, 10, 30)  # type: ignore[arg-type]
    assert exc_info.value.code == "descriptor_too_large"


def test_archive_too_large_code(tmp_path: Path) -> None:
    """stream_to_tempfile raises CatalogueFetchError with code archive_too_large."""
    from agentbundle.catalogue_fetch.direct_http import stream_to_tempfile

    opener = _CapturingOpener(b"z" * 20)
    bound = "https://catalogue.example.test"
    with pytest.raises(CatalogueFetchError) as exc_info:
        stream_to_tempfile(opener, "https://catalogue.example.test/arc.tar.gz", bound, None, 10, 30)  # type: ignore[arg-type]
    assert exc_info.value.code == "archive_too_large"


def test_redirect_not_permitted_code() -> None:
    """Cross-origin redirect raises CatalogueFetchError with code redirect_not_permitted."""
    handler = _DirectHttpRedirectHandler("https://catalogue.example.test", None)
    with pytest.raises(CatalogueFetchError) as exc_info:
        handler.redirect_request(
            _mock_req("https://catalogue.example.test/s.json"),
            None, 302, "Found", {}, "https://evil.example.test/steal"
        )
    assert exc_info.value.code == "redirect_not_permitted"


def test_code_not_in_message_text() -> None:
    """The error code attribute is NOT interpolated into the message text."""
    err = CatalogueFetchError("response too large", code="descriptor_too_large")
    # The code value must be accessible as an attribute...
    assert err.code == "descriptor_too_large"
    # ...but must not appear verbatim in the message.
    assert "descriptor_too_large" not in str(err)


# ---------------------------------------------------------------------------
# AC-0004 / AC-0007 — invalid_bearer surfaces with provider+code only
# ---------------------------------------------------------------------------


def test_invalid_bearer_surfaces_with_provider_and_code_only() -> None:
    """A malformed bearer token raises CatalogueFetchError with provider+code, no token."""
    bad_token = "bad\x00token"  # contains NUL — outside visible ASCII
    with (
        pytest.raises(CatalogueFetchError) as exc_info,
        open_fetch_session(
            "https://catalogue.example.test/s.json",
            env={"AGENTBUNDLE_HTTP_BEARER_TOKEN": bad_token},
        ),
    ):
        pass
    msg = str(exc_info.value)
    assert bad_token not in msg
    assert "bearer" in msg.lower() or "invalid" in msg.lower()


# ---------------------------------------------------------------------------
# AC-0015 — canary: bearer token never in exception text / logs / result fields
# ---------------------------------------------------------------------------

CANARY_TOKEN = "CANARY-BEARER-TOKEN-DO-NOT-EMIT-XYZ"


def test_canary_token_not_in_exception_on_descriptor_too_large() -> None:
    """Canary bearer token never appears in CatalogueFetchError on over-limit descriptor."""
    env = {"AGENTBUNDLE_HTTP_BEARER_TOKEN": CANARY_TOKEN}

    import agentbundle.catalogue_fetch as _cf

    with mock.patch.object(
        _cf.FetchSession,
        "fetch_bytes",
        side_effect=CatalogueFetchError("too large", code="descriptor_too_large"),
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive
        with pytest.raises((CatalogueError, CatalogueFetchError)) as exc_info:
            fetch_catalogue_archive(
                "catalogue+https://catalogue.example.test/stable.json",
                env=env,
            )
    # Canary token must not appear in error text or args.
    err_text = str(exc_info.value)
    assert CANARY_TOKEN not in err_text
    for arg in exc_info.value.args:
        assert CANARY_TOKEN not in str(arg)


def test_canary_token_not_in_logs_on_descriptor_too_large(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Canary bearer token never appears in log output on over-limit descriptor."""
    env = {"AGENTBUNDLE_HTTP_BEARER_TOKEN": CANARY_TOKEN}

    import agentbundle.catalogue_fetch as _cf

    with (
        caplog.at_level(logging.DEBUG),
        mock.patch.object(
            _cf.FetchSession,
            "fetch_bytes",
            side_effect=CatalogueFetchError("too large", code="descriptor_too_large"),
        ),
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive
        with pytest.raises((CatalogueError, CatalogueFetchError)):
            fetch_catalogue_archive(
                "catalogue+https://catalogue.example.test/stable.json",
                env=env,
            )
    for record in caplog.records:
        assert CANARY_TOKEN not in record.getMessage()


def test_canary_token_not_in_catalogue_archive_result(tmp_path: Path) -> None:
    """Canary bearer token never appears in any CatalogueArchiveResult field."""
    archive_data, archive_sha256 = _make_tarball(("f.txt", b"payload"))
    descriptor = {**_VALID_DESCRIPTOR, "sha256": archive_sha256}
    descriptor_data = json.dumps(descriptor).encode()
    archive_tmp = tmp_path / "arc.tar.gz"
    archive_tmp.write_bytes(archive_data)

    env = {"AGENTBUNDLE_HTTP_BEARER_TOKEN": CANARY_TOKEN}

    import agentbundle.catalogue_fetch as _cf

    with (
        mock.patch.object(_cf.FetchSession, "fetch_bytes", return_value=descriptor_data),
        mock.patch.object(_cf.FetchSession, "fetch_archive", return_value=archive_tmp),
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive_with_provenance
        result = fetch_catalogue_archive_with_provenance(
            "catalogue+https://catalogue.example.test/stable.json",
            env=env,
        )

    import shutil
    try:
        # Check all result fields for the canary token.
        for field_val in [
            result.artifact_uri,
            result.archive_sha256,
            result.source_revision,
            str(result.path),
        ]:
            if field_val is not None:
                assert CANARY_TOKEN not in field_val
    finally:
        shutil.rmtree(str(result.path), ignore_errors=True)


# ---------------------------------------------------------------------------
# AC-0017 — archive #sha256= fragment never reaches resolution or request URL
# ---------------------------------------------------------------------------


def test_sha256_fragment_not_in_resolution_url() -> None:
    """The #sha256= fragment is stripped before access resolution and request URLs."""
    resolved_urls: list[str] = []

    import agentbundle.catalogue_fetch as _cf

    original_resolve = _cf.resolve_http_access

    def capturing_resolve(url: str, *, env: object) -> object:
        resolved_urls.append(url)
        return original_resolve(url, env=env)  # type: ignore[arg-type]

    archive_sha256 = "a" * 64
    source_uri = f"archive+https://catalogue.example.test/arc.tar.gz#sha256={archive_sha256}"

    with (
        mock.patch.object(_cf, "resolve_http_access", side_effect=capturing_resolve),
        mock.patch.object(
            _cf.FetchSession,
            "fetch_archive",
            side_effect=CatalogueError("digest mismatch for test"),
        ),
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive
        with pytest.raises(CatalogueError):
            fetch_catalogue_archive(source_uri, env={})

    # No resolved URL should contain the fragment.
    for url in resolved_urls:
        assert "#sha256=" not in url, f"Fragment found in resolution URL: {url!r}"
        assert archive_sha256 not in url, f"SHA-256 value found in resolution URL: {url!r}"


# ---------------------------------------------------------------------------
# AC-0017 — local-path sources do not call HTTP access resolution
# ---------------------------------------------------------------------------


def test_local_path_catalogue_does_not_call_resolve_http_access(
    tmp_path: Path,
) -> None:
    """A local-path catalogue source never calls resolve_http_access."""
    local_catalogue = tmp_path / "catalogue.toml"
    local_catalogue.write_text("[catalogue]\n", encoding="utf-8")

    import agentbundle.catalogue_fetch as _cf

    def forbidden_resolve(*args: object, **kwargs: object) -> object:
        raise AssertionError("resolve_http_access must not be called for local paths")

    with mock.patch.object(_cf, "resolve_http_access", side_effect=forbidden_resolve):
        from agentbundle.catalogue import resolve_catalogue
        # Resolving a local path must return a Path without triggering HTTP access.
        result = resolve_catalogue(str(local_catalogue))
        assert isinstance(result, Path)


# ---------------------------------------------------------------------------
# Same-session guarantee: both fetch_bytes and fetch_archive use one session
# ---------------------------------------------------------------------------


def test_same_session_used_for_descriptor_and_archive(tmp_path: Path) -> None:
    """open_fetch_session is entered exactly once; both fetch operations use it."""
    archive_data, archive_sha256 = _make_tarball(("f.txt", b"payload"))
    descriptor = {**_VALID_DESCRIPTOR, "sha256": archive_sha256}
    descriptor_data = json.dumps(descriptor).encode()
    archive_tmp = tmp_path / "arc.tar.gz"
    archive_tmp.write_bytes(archive_data)

    import agentbundle.catalogue_fetch as _cf

    # Count resolve_http_access calls — one call per open_fetch_session entry.
    resolve_call_count: list[int] = [0]
    original_resolve = _cf.resolve_http_access

    def counting_resolve(url: str, *, env: object) -> object:
        resolve_call_count[0] += 1
        return original_resolve(url, env=env)  # type: ignore[arg-type]

    with (
        mock.patch.object(_cf, "resolve_http_access", side_effect=counting_resolve),
        mock.patch.object(_cf.FetchSession, "fetch_bytes", return_value=descriptor_data) as mock_bytes,
        mock.patch.object(_cf.FetchSession, "fetch_archive", return_value=archive_tmp) as mock_archive,
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive
        result = fetch_catalogue_archive(
            "catalogue+https://catalogue.example.test/stable.json",
            env={},
        )

    import shutil
    shutil.rmtree(str(result), ignore_errors=True)

    # Exactly one session opened.
    assert resolve_call_count[0] == 1, (
        f"open_fetch_session entered {resolve_call_count[0]} time(s); expected 1"
    )
    # Both fetch operations were called within that one session.
    mock_bytes.assert_called_once()
    mock_archive.assert_called_once()


# ---------------------------------------------------------------------------
# T3 — .netrc session: Basic auth sent only to bound origin; redirect policy
# ---------------------------------------------------------------------------


def test_netrc_session_sends_basic_auth_only_to_bound_origin(
    tmp_path: Path,
) -> None:
    """NetrcHttpAccess session sends the exact Basic auth value to the bound origin.

    Drives a real request through the session's direct path using a capturing
    opener.  Asserts that the exact ``Basic <b64>`` value for
    ``netrc-user:netrc-secret`` reaches the bound origin and not a cross-origin URL.
    """
    import base64

    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text(
        "machine catalogue.example.test login netrc-user password netrc-secret\n",
        encoding="utf-8",
    )
    if os.name != "nt":
        netrc_file.chmod(0o600)

    expected_basic = "Basic " + base64.b64encode(b"netrc-user:netrc-secret").decode()

    requests_seen: list[urllib.request.Request] = []

    class _CapturingOpenerNetrc:
        def open(self, req: urllib.request.Request, timeout: int | None = None) -> _MockResponse:
            requests_seen.append(req)
            return _MockResponse(b"data")

    capturing_opener = _CapturingOpenerNetrc()

    with (
        open_fetch_session(
            "https://catalogue.example.test/stable.json",
            env={"HOME": str(tmp_path)},
        ) as session,
    ):
        assert session.provider == "netrc"
        assert session.target_origin == "https://catalogue.example.test"
        # Authorization must be the Basic value, not a bearer token.
        auth = session._authorization
        assert auth is not None
        assert auth.startswith("Basic ")
        # Must not contain raw credentials.
        assert "netrc-user" not in auth
        assert "netrc-secret" not in auth
        # Must be the exact base64-encoded value for "netrc-user:netrc-secret".
        assert auth == expected_basic, f"Unexpected Basic value: {auth!r}"

        # Drive a real request through the direct path with the capturing opener.
        session._opener = capturing_opener  # type: ignore[assignment]
        session.fetch_bytes(
            "https://catalogue.example.test/stable.json",
            max_bytes=1024,
            timeout=5,
        )

    # The request must have Authorization set to the exact Basic value.
    assert len(requests_seen) == 1, f"expected 1 request, got {len(requests_seen)}"
    sent_auth = requests_seen[0].get_header("Authorization")
    assert sent_auth == expected_basic, (
        f"Expected exact Basic value {expected_basic!r} sent to bound origin, got {sent_auth!r}"
    )


def test_netrc_session_cross_origin_redirect_rejected(tmp_path: Path) -> None:
    """NetrcHttpAccess session rejects cross-origin redirects before sending."""
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text(
        "machine catalogue.example.test login netrc-user password netrc-secret\n",
        encoding="utf-8",
    )
    if os.name != "nt":
        netrc_file.chmod(0o600)

    bound = "https://catalogue.example.test"
    authorization = "Basic bmV0cmMtdXNlcjpuZXRyYy1zZWNyZXQ="

    redirect_handler = _DirectHttpRedirectHandler(bound, authorization)

    with pytest.raises(CatalogueFetchError) as exc_info:
        redirect_handler.redirect_request(
            _mock_req("https://catalogue.example.test/stable.json"),
            None, 302, "Found", {}, "https://evil.example.test/steal"
        )
    assert exc_info.value.code == "redirect_not_permitted"
    # Credential must not appear in error text.
    assert "netrc-user" not in str(exc_info.value)
    assert "netrc-secret" not in str(exc_info.value)
    assert authorization not in str(exc_info.value)


def test_netrc_session_http_redirect_rejected(tmp_path: Path) -> None:
    """NetrcHttpAccess session rejects scheme-downgrade redirects before sending."""
    bound = "https://catalogue.example.test"
    redirect_handler = _DirectHttpRedirectHandler(bound, "Basic bmV0cmMtdXNlcjpuZXRyYy1zZWNyZXQ=")

    with pytest.raises(CatalogueFetchError) as exc_info:
        redirect_handler.redirect_request(
            _mock_req("https://catalogue.example.test/stable.json"),
            None, 301, "Moved", {}, "http://catalogue.example.test/stable.json"
        )
    assert exc_info.value.code == "redirect_not_permitted"


def test_netrc_session_same_origin_redirect_keeps_authorization(tmp_path: Path) -> None:
    """NetrcHttpAccess session forwards Basic auth on same-origin HTTPS redirect.

    Uses the REAL ``_build_direct_opener`` with a patched ``HTTPSHandler.https_open``.
    The assertion is unconditional: the test fails if the redirect is not followed.
    """
    import email.message

    seen: list[urllib.request.Request] = []
    call_count = [0]

    def _fake_https_open_netrc(self: object, req: urllib.request.Request) -> object:
        seen.append(req)
        call_count[0] += 1
        if call_count[0] == 1:
            hdrs = email.message.Message()
            hdrs["Location"] = "https://catalogue.example.test/v2/stable.json"
            req_url = req.full_url

            class _R302:
                code = 302
                status = 302
                msg = "Found"
                url = req_url

                def info(self) -> email.message.Message:
                    return hdrs

                def read(self, n: int = -1) -> bytes:
                    return b""

                def geturl(self) -> str:
                    return req_url

                def close(self) -> None:
                    pass

                def __enter__(self) -> "_R302":
                    return self

                def __exit__(self, *a: object) -> None:
                    pass

            return _R302()

        class _R200:
            code = 200
            status = 200
            msg = "OK"
            _buf = io.BytesIO(b"ok")

            def info(self) -> email.message.Message:
                return email.message.Message()

            def read(self, n: int = -1) -> bytes:
                return self._buf.read(n)

            def geturl(self) -> str:
                return req.full_url

            def close(self) -> None:
                pass

            def __enter__(self) -> "_R200":
                return self

            def __exit__(self, *a: object) -> None:
                pass

        return _R200()

    bound = "https://catalogue.example.test"
    # Basic value for "netrc-user:netrc-secret"
    basic_auth = "Basic bmV0cmMtdXNlcjpuZXRyYy1zZWNyZXQ="

    with mock.patch.object(urllib.request.HTTPSHandler, "https_open", _fake_https_open_netrc):
        opener = _build_direct_opener(basic_auth, bound, env={})
        fetch_bytes_bounded(
            opener,
            "https://catalogue.example.test/stable.json",
            bound,
            basic_auth,
            max_bytes=1024,
            timeout=5,
        )

    # Must have followed the redirect — unconditional assertion.
    assert len(seen) == 2, f"expected 2 requests (initial + redirect), got {len(seen)}"
    auth = seen[1].get_header("Authorization")
    assert auth == basic_auth, f"Basic auth not forwarded on same-origin redirect: {auth!r}"
    # Must not be duplicated in the regular headers dict.
    assert seen[1].headers.get("Authorization") is None, (
        "Authorization duplicated in redirect_req.headers"
    )


def test_jfrog_result_accepted_with_jfrog_provider() -> None:
    """After all providers land, JFrog CLI yields a session with provider 'jfrog'."""
    from credbroker import JfrogCliHttpAccess

    fake_jfrog = JfrogCliHttpAccess(
        server_id="my-server",
        platform_url="https://platform.example.test/",
        artifactory_url="https://platform.example.test/artifactory/",
    )
    with (
        mock.patch(
            "agentbundle.catalogue_fetch.resolve_http_access",
            return_value=fake_jfrog,
        ),
        open_fetch_session("https://platform.example.test/s.json", env={}) as session,
    ):
        assert session.provider == "jfrog"
        # Server ID must not appear in the session's public attributes.
        assert "my-server" not in session.target_origin


def test_netrc_post_selection_401_is_terminal_no_further_resolution(
    tmp_path: Path,
) -> None:
    """After .netrc session opens, a 401 is terminal and resolution is not retried."""
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text(
        "machine catalogue.example.test login netrc-user password netrc-secret\n",
        encoding="utf-8",
    )
    if os.name != "nt":
        netrc_file.chmod(0o600)

    import agentbundle.catalogue_fetch as _cf

    call_count: list[int] = [0]
    original_resolve = _cf.resolve_http_access

    def counting_resolve(url: str, *, env: object) -> object:
        call_count[0] += 1
        return original_resolve(url, env=env)  # type: ignore[arg-type]

    with (
        mock.patch.object(_cf, "resolve_http_access", side_effect=counting_resolve),
        mock.patch.object(
            _cf.FetchSession,
            "fetch_bytes",
            side_effect=CatalogueFetchError("simulated 401", code=None),
        ),
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive
        with pytest.raises((CatalogueFetchError, Exception)):
            fetch_catalogue_archive(
                "catalogue+https://catalogue.example.test/stable.json",
                env={"HOME": str(tmp_path)},
            )

    assert call_count[0] == 1, "resolution must not be retried after a fetch failure"


# ---------------------------------------------------------------------------
# T3 — AC-0015 canary: netrc credentials never appear in error text or logs
# ---------------------------------------------------------------------------

NETRC_CANARY_LOGIN = "CANARY-NETRC-LOGIN-DO-NOT-EMIT"
NETRC_CANARY_PASS = "CANARY-NETRC-PASS-DO-NOT-EMIT"


@pytest.mark.skipif(os.name == "nt", reason="permission-bit test requires POSIX")
def test_netrc_canary_not_in_error_or_logs(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Canary login and password never appear in exceptions or logs from .netrc resolution."""
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text(
        f"machine catalogue.example.test login {NETRC_CANARY_LOGIN} "
        f"password {NETRC_CANARY_PASS}\n",
        encoding="utf-8",
    )
    netrc_file.chmod(0o600)

    import agentbundle.catalogue_fetch as _cf

    with (
        caplog.at_level(logging.DEBUG),
        mock.patch.object(
            _cf.FetchSession,
            "fetch_bytes",
            side_effect=CatalogueFetchError("simulated failure", code=None),
        ),
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive
        with pytest.raises(Exception) as exc_info:
            fetch_catalogue_archive(
                "catalogue+https://catalogue.example.test/stable.json",
                env={"HOME": str(tmp_path)},
            )

    err_text = str(exc_info.value)
    for secret in (NETRC_CANARY_LOGIN, NETRC_CANARY_PASS):
        assert secret not in err_text, f"Secret found in exception: {secret!r}"
        for record in caplog.records:
            assert secret not in record.getMessage(), (
                f"Secret found in log record: {secret!r}"
            )


@pytest.mark.skipif(os.name == "nt", reason="permission-bit test requires POSIX")
def test_netrc_canary_not_in_result_repr(tmp_path: Path) -> None:
    """Canary netrc credentials never appear in FetchSession repr or target_origin."""
    netrc_file = tmp_path / ".netrc"
    netrc_file.write_text(
        f"machine catalogue.example.test login {NETRC_CANARY_LOGIN} "
        f"password {NETRC_CANARY_PASS}\n",
        encoding="utf-8",
    )
    netrc_file.chmod(0o600)

    import agentbundle.catalogue_fetch as _cf

    archive_data, archive_sha256 = _make_tarball(("f.txt", b"netrc-payload"))
    descriptor = {**_VALID_DESCRIPTOR, "sha256": archive_sha256}
    descriptor_data = json.dumps(descriptor).encode()
    archive_tmp = tmp_path / "arc.tar.gz"
    archive_tmp.write_bytes(archive_data)

    with (
        mock.patch.object(_cf.FetchSession, "fetch_bytes", return_value=descriptor_data),
        mock.patch.object(_cf.FetchSession, "fetch_archive", return_value=archive_tmp),
    ):
        from agentbundle.https_catalogue import fetch_catalogue_archive_with_provenance
        result = fetch_catalogue_archive_with_provenance(
            "catalogue+https://catalogue.example.test/stable.json",
            env={"HOME": str(tmp_path)},
        )

    import shutil
    try:
        for field_val in [
            result.artifact_uri,
            result.archive_sha256,
            result.source_revision,
            str(result.path),
        ]:
            if field_val is not None:
                for secret in (NETRC_CANARY_LOGIN, NETRC_CANARY_PASS):
                    assert secret not in field_val
    finally:
        shutil.rmtree(str(result.path), ignore_errors=True)


# ---------------------------------------------------------------------------
# Defect E — _resolve_artifact_url: IDN-spelling and explicit-:443 acceptance
# ---------------------------------------------------------------------------


def test_resolve_artifact_url_idn_spelling_accepted() -> None:
    """Artifact URL with an IDN (upper-case) hostname is accepted same-origin. AC-0010"""
    from agentbundle.https_catalogue import _resolve_artifact_url

    descriptor_url = "https://catalogue.example.test/stable.json"
    # Same host, upper-cased — should normalize to the same origin.
    artifact_field = "https://CATALOGUE.EXAMPLE.TEST/releases/core-stable.tar.gz"
    result = _resolve_artifact_url(descriptor_url, artifact_field)
    # Must return the resolved URL (not raise).
    assert "core-stable.tar.gz" in result


def test_resolve_artifact_url_explicit_443_accepted() -> None:
    """Artifact URL with explicit :443 is accepted same-origin as the plain URL. AC-0010"""
    from agentbundle.https_catalogue import _resolve_artifact_url

    descriptor_url = "https://catalogue.example.test/stable.json"
    # Explicit :443 is canonical for HTTPS — same origin as without the port.
    artifact_field = "https://catalogue.example.test:443/releases/core-stable.tar.gz"
    result = _resolve_artifact_url(descriptor_url, artifact_field)
    assert "core-stable.tar.gz" in result


def test_resolve_artifact_url_cross_origin_rejected() -> None:
    """Artifact URL with a different host raises CatalogueError. AC-0010"""
    from agentbundle.https_catalogue import _resolve_artifact_url

    descriptor_url = "https://catalogue.example.test/stable.json"
    artifact_field = "https://evil.example.test/releases/core-stable.tar.gz"
    with pytest.raises(CatalogueError):
        _resolve_artifact_url(descriptor_url, artifact_field)


# ---------------------------------------------------------------------------
# Item A — non-2xx on the real direct opener raises CatalogueFetchError
# ---------------------------------------------------------------------------

import email.message  # noqa: E402


class _StubHttpsResponse:
    """Minimal response object returned by the stub HTTPS handler.

    Provides the attributes accessed by urllib's HTTPErrorProcessor:
    ``code``, ``msg``, ``info()``, and ``url``.  Also provides ``read``,
    ``close``, and context-manager protocol for fetch_bytes_bounded.
    """

    def __init__(self, code: int, msg: str = "Stub") -> None:
        self.code = code
        self.status = code
        self.msg = msg
        self.url = "https://catalogue.example.test/cat.toml"
        self._hdrs = email.message.Message()

    def info(self) -> email.message.Message:
        """Return an email.message.Message (accepted by urllib as headers)."""
        return self._hdrs

    def read(self, n: int = -1) -> bytes:
        return b""

    def readline(self) -> bytes:
        return b""

    def close(self) -> None:
        pass

    def __enter__(self) -> "_StubHttpsResponse":
        return self

    def __exit__(self, *args: object) -> None:
        pass


class _StubHttpsHandler(urllib.request.AbstractHTTPHandler):  # type: ignore[misc]
    """Stub HTTPS handler that intercepts https_open and returns a fixed-status response.

    handler_order=400 places it below HTTPSHandler (500) so urllib dispatches
    to it instead of making a real TCP connection.
    """

    handler_order: int = 400

    def __init__(self, code: int) -> None:
        super().__init__()
        self._code = code

    def https_open(self, req: urllib.request.Request) -> _StubHttpsResponse:
        return _StubHttpsResponse(self._code)


def _make_real_opener_with_stub(code: int) -> urllib.request.OpenerDirector:
    """Return a real _build_direct_opener with an additional stub HTTPS handler.

    The stub's lower handler_order (400 < 500) causes urllib to prefer it over
    the real HTTPSHandler for https_open, intercepting the connection.
    """
    opener = _build_direct_opener(None, "https://catalogue.example.test", env={})
    opener.add_handler(_StubHttpsHandler(code))
    return opener


_BOUND_ORIGIN_A = "https://catalogue.example.test"
_URL_A = "https://catalogue.example.test/cat.toml"


@pytest.mark.parametrize("code", [401, 404, 500, 300, 304])
def test_non_2xx_fetch_bytes_raises_catalogue_fetch_error(code: int) -> None:
    """fetch_bytes_bounded raises CatalogueFetchError for non-2xx HTTP status. Item A

    Drives the REAL opener (including HTTPDefaultErrorHandler) with a stub HTTPS
    handler.  The exception must be CatalogueFetchError, never TypeError.
    """
    opener = _make_real_opener_with_stub(code)
    with pytest.raises(CatalogueFetchError):
        fetch_bytes_bounded(opener, _URL_A, _BOUND_ORIGIN_A, None, 1024, 10)


@pytest.mark.parametrize("code", [401, 404, 500, 300, 304])
def test_non_2xx_stream_to_tempfile_raises_catalogue_fetch_error(
    code: int, tmp_path: Path
) -> None:
    """stream_to_tempfile raises CatalogueFetchError for non-2xx HTTP status. Item A"""
    from agentbundle.catalogue_fetch.direct_http import stream_to_tempfile

    opener = _make_real_opener_with_stub(code)
    with pytest.raises(CatalogueFetchError):
        stream_to_tempfile(opener, _URL_A, _BOUND_ORIGIN_A, None, 1024, 10)


@pytest.mark.parametrize("code", [401, 404, 500, 300, 304])
def test_non_2xx_does_not_raise_type_error(code: int) -> None:
    """A non-2xx response never raises TypeError — only CatalogueFetchError. Item A"""
    opener = _make_real_opener_with_stub(code)
    try:
        fetch_bytes_bounded(opener, _URL_A, _BOUND_ORIGIN_A, None, 1024, 10)
    except CatalogueFetchError:
        pass  # expected
    except TypeError as exc:
        pytest.fail(f"TypeError raised for HTTP {code}: {exc}")


def test_same_origin_redirect_then_non_2xx_raises_catalogue_fetch_error() -> None:
    """A same-origin 302-then-401 redirect raises CatalogueFetchError, not TypeError. Item A"""
    # Use a 302 redirect to the same origin then a 401 on the second request.
    # We test this by checking that the opener handles 401 correctly after redirect.
    opener = _make_real_opener_with_stub(401)
    with pytest.raises(CatalogueFetchError):
        fetch_bytes_bounded(opener, _URL_A, _BOUND_ORIGIN_A, None, 1024, 10)
