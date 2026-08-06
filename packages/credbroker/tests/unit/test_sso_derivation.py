"""Server-attested sign-in destination — the strategy chain and its bounds.

Covers AC32 of ``docs/specs/jira-check-sso-auto-login/spec.md``.

``derive_sso_destination`` asks the *resource server* where to authenticate,
rather than trusting the configured value. It is **defence in depth, not the
control**: the derivation target (``base_url``) lives in the same
agent-writable file as the value being attested, so one write moves both.
Consent for first capture rests on the operation being operator-typed.

Two test surfaces, because they prove different things:

* the **chain** is driven through a fake opener — canned status, headers and
  body per URL — which is what makes the tier ordering, the scheme guard, the
  budget and the body cap assertable;
* the **real opener** is driven against a local server, because "redirects are
  not followed" is a property of the handler stack and nothing else can prove
  it. That one test speaks plain HTTP deliberately: it calls the opener
  directly, past the https guard, since the guard is what the other tests
  cover.
"""

from __future__ import annotations

import http.server
import json
import ssl
import threading
import urllib.error
import urllib.request

import credbroker
import pytest
from credbroker import _sso

BASE = "https://jira.corp.example.com"
IDP = "https://idp.corp.example.com"


class _Canned:
    """One canned HTTP answer."""

    def __init__(self, status=200, headers=None, body=b""):
        self.status = status
        self.headers = headers or {}
        self.body = body

    @classmethod
    def json(cls, payload, status=200):
        return cls(status=status, body=json.dumps(payload).encode("utf-8"))


class _FakeOpener:
    """Maps URL -> canned answer, and records every URL actually fetched."""

    def __init__(self, routes: dict[str, _Canned]):
        self.routes = routes
        self.fetched: list[str] = []

    def install(self, monkeypatch):
        outer = self

        def _open(url, budget):
            outer.fetched.append(url)
            canned = outer.routes.get(url)
            if canned is None:
                raise _sso._DerivationAbort(f"no route for {url}")
            return _sso._DerivationResponse(canned.status, canned.headers, canned.body)

        monkeypatch.setattr(_sso, "_derive_open", _open)
        return self


# ----------------------------------------------------------------------
# The tier chain.
# ----------------------------------------------------------------------


def test_tier1_protected_resource_metadata(monkeypatch):        # STUB: AC32
    # RFC 9728: 401 -> resource_metadata -> authorization_servers -> AS metadata
    # -> authorization_endpoint. The modern standard; adopted by MCP.
    opener = _FakeOpener({
        BASE: _Canned(
            401,
            {"WWW-Authenticate": f'Bearer resource_metadata="{BASE}/.well-known/oauth-protected-resource"'},
        ),
        f"{BASE}/.well-known/oauth-protected-resource": _Canned.json(
            {"authorization_servers": [IDP]}
        ),
        f"{IDP}/.well-known/oauth-authorization-server": _Canned.json(
            {"authorization_endpoint": f"{IDP}/authorize?state=abc"}
        ),
    }).install(monkeypatch)

    assert credbroker.derive_sso_destination(BASE) == IDP
    assert f"{IDP}/.well-known/oauth-authorization-server" in opener.fetched


def test_tier2_oidc_discovery(monkeypatch):                     # STUB: AC32
    # Older than tier 1, and far more widely deployed today.
    _FakeOpener({
        BASE: _Canned(200),
        f"{BASE}/.well-known/openid-configuration": _Canned.json(
            {"authorization_endpoint": f"{IDP}/oauth2/authorize?nonce=1"}
        ),
    }).install(monkeypatch)

    assert credbroker.derive_sso_destination(BASE) == IDP


def test_derives_login_host_from_login_jsp(monkeypatch):        # STUB: AC32
    # Verified by live spike: GET https://jira.atlassian.com/login.jsp -> 302,
    # Location: https://auth.atlassian.com/authorize?...
    _FakeOpener({
        BASE: _Canned(200),
        f"{BASE}/.well-known/openid-configuration": _Canned(404),
        f"{BASE}/login.jsp": _Canned(302, {"Location": f"{IDP}/authorize?state=abc"}),
    }).install(monkeypatch)

    assert credbroker.derive_sso_destination(
        BASE, strategies=("atlassian-seraph",)
    ) == IDP


def test_vendor_probe_is_opt_in(monkeypatch):                   # STUB: AC32
    # A non-Atlassian consumer must never run the Seraph probe.
    opener = _FakeOpener({
        BASE: _Canned(200),
        f"{BASE}/.well-known/openid-configuration": _Canned(404),
        f"{BASE}/login.jsp": _Canned(302, {"Location": f"{IDP}/authorize"}),
    }).install(monkeypatch)

    assert credbroker.derive_sso_destination(BASE) is None
    assert f"{BASE}/login.jsp" not in opener.fetched


def test_unknown_strategy_is_refused():                         # STUB: AC32
    with pytest.raises(credbroker.SsoConfigError):
        credbroker.derive_sso_destination(BASE, strategies=("no-such-strategy",))


def test_cannot_derive_returns_none(monkeypatch):               # STUB: AC32
    # SSO-with-local-fallback: login.jsp answers 200 with a sign-in button and
    # no Location. A real outcome (tier 4), not a failure to handle.
    _FakeOpener({
        BASE: _Canned(200),
        f"{BASE}/.well-known/openid-configuration": _Canned(404),
        f"{BASE}/login.jsp": _Canned(200),
    }).install(monkeypatch)

    assert credbroker.derive_sso_destination(
        BASE, strategies=("atlassian-seraph",)
    ) is None


def test_only_scheme_and_host_are_returned(monkeypatch):        # STUB: AC32
    # Every tier's URL carries per-request state / SAMLRequest / nonce values
    # that change on each call, so only scheme+host can be compared.
    _FakeOpener({
        BASE: _Canned(200),
        f"{BASE}/.well-known/openid-configuration": _Canned.json(
            {"authorization_endpoint": f"{IDP}/authorize?state=abc&nonce=xyz"}
        ),
    }).install(monkeypatch)

    assert credbroker.derive_sso_destination(BASE) == IDP


def test_a_failing_tier_does_not_abort_the_chain(monkeypatch):  # STUB: AC32
    _FakeOpener({
        # tier 1 unroutable -> abort; tier 2 must still run
        f"{BASE}/.well-known/openid-configuration": _Canned.json(
            {"authorization_endpoint": f"{IDP}/authorize"}
        ),
    }).install(monkeypatch)

    assert credbroker.derive_sso_destination(BASE) == IDP


# ----------------------------------------------------------------------
# Bounds — this is an outbound fetch on the credential path.
# ----------------------------------------------------------------------


@pytest.mark.parametrize("hostile", [
    "http://idp.corp.example.com/authorize",
    "file:///etc/passwd",
    "ftp://idp.corp.example.com/x",
])
def test_non_https_at_any_hop_is_rejected(monkeypatch, hostile):   # STUB: AC32
    # Tier 1 fetches a URL taken from a *response header* and then a second from
    # that document — two attacker-influenceable targets. urllib honours
    # file:// and ftp://.
    opener = _FakeOpener({
        BASE: _Canned(401, {"WWW-Authenticate": f'Bearer resource_metadata="{hostile}"'}),
        f"{BASE}/.well-known/openid-configuration": _Canned(404),
    }).install(monkeypatch)
    # The fake opener records fetches but the *real* scheme guard lives in
    # _derive_open, so drive that directly for the hop itself.
    monkeypatch.undo()
    with pytest.raises(_sso._DerivationAbort):
        _sso._derive_open(hostile, _sso._DerivationBudget(15.0))
    del opener


def test_authorization_servers_entries_are_scheme_checked(monkeypatch):  # STUB: AC32
    opener = _FakeOpener({
        BASE: _Canned(
            401,
            {"WWW-Authenticate": f'Bearer resource_metadata="{BASE}/.well-known/oauth-protected-resource"'},
        ),
        f"{BASE}/.well-known/oauth-protected-resource": _Canned.json(
            {"authorization_servers": ["http://idp.corp.example.com"]}
        ),
        f"{BASE}/.well-known/openid-configuration": _Canned(404),
    }).install(monkeypatch)

    assert credbroker.derive_sso_destination(BASE) is None
    assert not any(u.startswith("http://") for u in opener.fetched)


def test_a_non_https_authorization_endpoint_is_dropped(monkeypatch):  # STUB: AC32
    _FakeOpener({
        BASE: _Canned(200),
        f"{BASE}/.well-known/openid-configuration": _Canned.json(
            {"authorization_endpoint": "http://idp.corp.example.com/authorize"}
        ),
    }).install(monkeypatch)
    assert credbroker.derive_sso_destination(BASE) is None


def test_body_is_capped_before_parsing():                       # STUB: AC32
    class _Fp:
        def read(self, n):
            return b"x" * n

        def close(self):
            pass

    with pytest.raises(_sso._DerivationAbort):
        _sso._read_capped(_Fp())


def test_a_drip_feeding_server_cannot_outrun_the_budget():      # STUB: AC32
    # The socket timeout applies per `recv`, so one large `read(cap + 1)` lets a
    # server that sends a byte at a time reset the clock forever — bounded only
    # by cap x timeout, which is hours. The budget must be re-checked *during*
    # the read, not only before the hop.
    import time as _time

    class _Drip:
        def __init__(self):
            self.reads = 0

        def read(self, n):
            self.reads += 1
            _time.sleep(0.001)   # a byte at a time, slowly — forever
            return b"x"

        def close(self):
            pass

    drip = _Drip()
    started = _time.monotonic()
    with pytest.raises(_sso._DerivationAbort):
        _sso._read_capped(drip, _sso._DerivationBudget(0.2))
    elapsed = _time.monotonic() - started

    # It gave up on the clock, not on the cap — and promptly.
    assert drip.reads < _sso._DERIVE_BODY_CAP_BYTES
    assert elapsed < 5, f"read ran {elapsed:.1f}s past a 0.2s budget"


def test_a_healthy_body_still_reads_whole():                    # STUB: AC32
    payload = b'{"authorization_endpoint": "https://idp.example/authorize"}'

    class _Fp:
        def __init__(self):
            self.rest = payload

        def read(self, n):
            head, self.rest = self.rest[:n], self.rest[n:]
            return head

        def close(self):
            pass

    assert _sso._read_capped(_Fp(), _sso._DerivationBudget(15.0)) == payload


def test_a_malformed_response_is_an_abort_not_a_traceback(monkeypatch):  # STUB: AC32
    # http.client.HTTPException (IncompleteRead, LineTooLong) is neither OSError
    # nor ValueError and is raised during the body read, after urllib has
    # finished wrapping transport errors — so without it in the except tuple a
    # malformed response escapes derivation entirely.
    import http.client

    class _Opener:
        def open(self, req, timeout=None):
            raise http.client.IncompleteRead(b"partial")

    monkeypatch.setattr(_sso, "_derivation_opener", lambda: _Opener())
    with pytest.raises(_sso._DerivationAbort):
        _sso._derive_open(f"{BASE}/x", _sso._DerivationBudget(15.0))
    # And the public entry point degrades to cannot-derive rather than raising.
    assert credbroker.derive_sso_destination(BASE) is None


def test_total_budget_is_enforced():                            # STUB: AC32
    budget = _sso._DerivationBudget(0.0)
    with pytest.raises(_sso._DerivationAbort):
        _sso._derive_open(f"{BASE}/x", budget)


def test_budget_and_socket_timeouts_match_the_spec():           # STUB: AC32
    assert _sso._DERIVE_TOTAL_BUDGET_S == 15.0
    assert _sso._DERIVE_SOCKET_TIMEOUT_S == 5.0
    assert _sso._DERIVE_BODY_CAP_BYTES == 64 * 1024


def test_no_auth_headers_on_the_wire(monkeypatch):              # STUB: AC32
    seen: dict = {}

    class _Opener:
        def open(self, req, timeout=None):
            seen["headers"] = dict(req.header_items())
            raise urllib.error.URLError("stop here")

    monkeypatch.setattr(_sso, "_derivation_opener", lambda: _Opener())
    with pytest.raises(_sso._DerivationAbort):
        _sso._derive_open(f"{BASE}/x", _sso._DerivationBudget(15.0))

    lowered = {k.lower() for k in seen["headers"]}
    for banned in ("authorization", "cookie", "proxy-authorization"):
        assert banned not in lowered


def test_tls_verification_is_strict_and_not_borrowed():         # STUB: AC32
    # Never honours an --insecure-style flag and never reuses a consumer's own
    # TLS context. Built explicitly so a process-wide
    # `ssl._create_default_https_context` override cannot weaken it.
    ctx = _sso._derivation_ssl_context()
    assert ctx.verify_mode == ssl.CERT_REQUIRED
    assert ctx.check_hostname is True


def test_proxy_credentials_are_stripped():                      # STUB: AC32
    stripped = _sso._proxies_without_credentials({
        "https": "http://user:secret@proxy.corp.example.com:8080",
        "http": "http://proxy.corp.example.com:8080",
    })
    assert "secret" not in stripped["https"]
    assert "user" not in stripped["https"]
    assert stripped["https"] == "http://proxy.corp.example.com:8080"
    assert stripped["http"] == "http://proxy.corp.example.com:8080"


def test_real_opener_does_not_follow_redirects():               # STUB: AC32
    # A property of the handler stack, so it needs the real opener. Plain HTTP
    # deliberately: this calls the opener directly, past the https guard the
    # other tests cover, because a local TLS listener would need a cert.
    hits: list[str] = []

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):                       # noqa: N802 — stdlib contract
            hits.append(self.path)
            if self.path == "/login.jsp":
                self.send_response(302)
                self.send_header("Location", "/followed")
                self.end_headers()
            else:
                self.send_response(200)
                self.end_headers()

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/login.jsp"
        req = urllib.request.Request(url, headers=_sso._DERIVE_HEADERS)
        with pytest.raises(urllib.error.HTTPError) as exc:
            _sso._derivation_opener().open(req, timeout=5)
        assert exc.value.code == 302
        assert exc.value.headers.get("Location") == "/followed"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert hits == ["/login.jsp"], f"the redirect was followed: {hits}"
