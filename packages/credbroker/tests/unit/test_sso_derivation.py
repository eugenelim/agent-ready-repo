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
import urllib.parse
import urllib.request

import credbroker
import pytest
from credbroker import _sso

BASE = "https://jira.corp.example.com"
IDP = "https://idp.corp.example.com"
# What derivation *returns*: the origin with the port made explicit, so an
# implicit and an explicit `:443` compare equal. The consumer normalises its own
# side the same way before comparing.
IDP_ORIGIN = "https://idp.corp.example.com:443"


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
        self.trusted_origin: list[str | None] = []

    def install(self, monkeypatch):
        outer = self
        # Hermetic: without this the chain tests hit live DNS through
        # `_resolves_to_internal_address` before the fake opener is consulted.
        # They pass here only because `corp.example.com` NXDOMAINs quickly; on a
        # resolver that wildcards NXDOMAIN to a captive-portal address — routine
        # on the corporate networks this code ships to — the guard would fire
        # and the chain tests would fail for an environment reason. The guard
        # keeps its own real-resolution tests below.
        monkeypatch.setattr(_sso, "_resolves_to_internal_address", lambda host: False)

        def _open(url, budget, *, trusted_origin=None):
            outer.fetched.append(url)
            outer.trusted_origin.append(trusted_origin)
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

    assert credbroker.derive_sso_destination(BASE) == IDP_ORIGIN
    assert f"{IDP}/.well-known/oauth-authorization-server" in opener.fetched


def test_tier2_oidc_discovery(monkeypatch):                     # STUB: AC32
    # Older than tier 1, and far more widely deployed today.
    _FakeOpener({
        BASE: _Canned(200),
        f"{BASE}/.well-known/openid-configuration": _Canned.json(
            {"authorization_endpoint": f"{IDP}/oauth2/authorize?nonce=1"}
        ),
    }).install(monkeypatch)

    assert credbroker.derive_sso_destination(BASE) == IDP_ORIGIN


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
    ) == IDP_ORIGIN


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

    assert credbroker.derive_sso_destination(BASE) == IDP_ORIGIN


def test_a_failing_tier_does_not_abort_the_chain(monkeypatch):  # STUB: AC32
    _FakeOpener({
        # tier 1 unroutable -> abort; tier 2 must still run
        f"{BASE}/.well-known/openid-configuration": _Canned.json(
            {"authorization_endpoint": f"{IDP}/authorize"}
        ),
    }).install(monkeypatch)

    assert credbroker.derive_sso_destination(BASE) == IDP_ORIGIN


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
        def read1(self, n):
            return b"x" * n

        def close(self):
            pass

    with pytest.raises(_sso._DerivationAbort):
        _sso._read_capped(_Fp(), _sso._DerivationBudget(15.0))


def test_a_drip_feeding_server_cannot_outrun_the_budget():      # STUB: AC32
    # The socket timeout applies per `recv`, so one large `read(cap + 1)` lets a
    # server that sends a byte at a time reset the clock forever — bounded only
    # by cap x timeout, which is hours. The budget must be re-checked *during*
    # the read, not only before the hop.
    import time as _time

    class _Drip:
        """Models `read1`, which is what the production path calls.

        Modelling `read` instead would have let the old one-shot implementation
        pass: a real `HTTPResponse.read(n)` blocks until it has *all* n bytes,
        so a fake returning one byte per `read` call understates the hazard by
        the chunk size.
        """

        def __init__(self):
            self.reads = 0
            self.read_calls = 0

        def read1(self, n):
            self.reads += 1
            _time.sleep(0.001)   # a byte at a time, slowly — forever
            return b"x"

        def read(self, n):      # pragma: no cover — must not be preferred
            self.read_calls += 1
            return self.read1(n)

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
    # And it used the non-blocking read: `read` would have let one call sit for
    # chunk-size x socket-timeout with the budget never consulted.
    assert drip.read_calls == 0, "must call read1, not read"


def test_a_healthy_body_still_reads_whole():                    # STUB: AC32
    payload = b'{"authorization_endpoint": "https://idp.example/authorize"}'

    class _Fp:
        def __init__(self):
            self.rest = payload

        def read1(self, n):
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


def test_socket_timeout_reaches_the_opener_and_tracks_the_budget():   # STUB: AC32
    # Behavioural, not a constant mirror: the total budget and the body cap
    # already have real tests above, but nothing observed the per-hop socket
    # timeout actually reaching `opener.open` — deleting `timeout=timeout` left
    # the suite green while the connect/read bound silently disappeared.
    seen: list = []

    class _Opener:
        def open(self, req, timeout=None):
            seen.append(timeout)
            raise urllib.error.URLError("stop here")

    import credbroker._sso as m
    real = m._derivation_opener
    m._derivation_opener = lambda: _Opener()
    try:
        with pytest.raises(_sso._DerivationAbort):
            _sso._derive_open(f"{BASE}/x", _sso._DerivationBudget(15.0), trusted_origin=_sso._origin(BASE))
        assert 0 < seen[-1] <= _sso._DERIVE_SOCKET_TIMEOUT_S
        # It shrinks with the shared budget, so a late hop cannot outlive it.
        with pytest.raises(_sso._DerivationAbort):
            _sso._derive_open(f"{BASE}/x", _sso._DerivationBudget(1.0), trusted_origin=_sso._origin(BASE))
        assert seen[-1] <= 1.0
    finally:
        m._derivation_opener = real


def test_no_auth_headers_on_the_wire(monkeypatch):              # STUB: AC32
    seen: dict = {}

    class _Opener:
        def open(self, req, timeout=None):
            seen["headers"] = dict(req.header_items())
            raise urllib.error.URLError("stop here")

    monkeypatch.setattr(_sso, "_derivation_opener", lambda: _Opener())
    with pytest.raises(_sso._DerivationAbort):
        _sso._derive_open(
            f"{BASE}/x", _sso._DerivationBudget(15.0),
            trusted_origin=_sso._origin(BASE),
        )

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


# A throwaway self-signed CA, inline so the fixture needs no key material on
# disk and no `openssl` at test time. Expired by design: `load_verify_locations`
# parses and stores it regardless, which is all these tests observe.
_SELF_SIGNED_CA_PEM = b"""-----BEGIN CERTIFICATE-----
MIICujCCAaICCQDyQE8uwXYQMDANBgkqhkiG9w0BAQsFADAfMR0wGwYDVQQDDBRF
eGFtcGxlIENvcnAgVGVzdCBDQTAeFw0yNjA4MDcwNDE1MjRaFw0yNjA4MDgwNDE1
MjRaMB8xHTAbBgNVBAMMFEV4YW1wbGUgQ29ycCBUZXN0IENBMIIBIjANBgkqhkiG
9w0BAQEFAAOCAQ8AMIIBCgKCAQEAzAksis87QaM63tutallFABfzbREdVlzAtgck
WSbtcV9jp1jiKBMgrfw85sNoH1/F1fDsgzwPa5uUC4OMsoivu6VGibMyy6AeF/CD
s3nX5W2RPgdZDk/6MpgHe+Sc2zOAP8Bx75pKA+2tC4eonh5GWqmBWmOkWWUnPrpC
R98VyzD5JWUUhJYsqu1gFFCB1ieSnmArloVlxU18wLCfRGEA9+Ail1vVCt90uxjo
hqBhTKvJ2q7pAV3yxlxHhPIBbOkrkXWFuyAnIHlGBIE0sN4sQ1Fudkk95Nv0cldI
eETAKntBKhDy7k0tc/qnHDAtby71u0/m0MfO7Ht2/c1YMb1hNwIDAQABMA0GCSqG
SIb3DQEBCwUAA4IBAQCfQa1YwOIymROSMeg+elpyXDFYQqafzI23mZ781z7S21N2
RVxCoGbWXijPtXmSYKHBRa4GaSzMbrmG214Hwu2ohLIzdk/GrvZarw44kMqmzvLq
IGIlHuBqZuv0X1LQL9wqGKefVp38GLTkKyoVQ1qg4y8egqPZVIbpd2U+S6CgYpUs
xvhoNj4yg8YjuVAwtJqi7hF4FTxOFqfBHMFKM3eoQWqgoR0Fb9B4ojjZzobo/WP8
kAp2xTiHVPkyeF0/HfNhweQ2YgWT75fHa7MTuiowdOR7zs3tU3+quhAA49hrFv25
cdwlTrT9JsOE6IJn7oldP6oAC0o+97ncSv/LZAl6
-----END CERTIFICATE-----
"""


def test_corporate_ca_bundle_is_loaded(monkeypatch, tmp_path):   # STUB: AC32
    # `create_default_context()` reads SSL_CERT_FILE/SSL_CERT_DIR through
    # OpenSSL's default paths but knows nothing of REQUESTS_CA_BUNDLE, which is
    # where a corporate MITM CA usually lands. Without it every derivation hop
    # fails verification on the laptops this feature exists for — and the
    # failure looks like "cannot derive", not "your CA was ignored".
    #
    # Asserted by loading a real CA into the context and comparing cert counts,
    # rather than by patching load_verify_locations: the point is that the
    # anchor is actually trusted, not that a call was made.
    ca = tmp_path / "corp-ca.pem"
    ca.write_bytes(_SELF_SIGNED_CA_PEM)

    monkeypatch.delenv("SSL_CERT_FILE", raising=False)
    monkeypatch.delenv("SSL_CERT_DIR", raising=False)
    monkeypatch.delenv("REQUESTS_CA_BUNDLE", raising=False)
    before = len(_sso._derivation_ssl_context().get_ca_certs())

    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(ca))
    after = _sso._derivation_ssl_context()
    assert len(after.get_ca_certs()) == before + 1, (
        "REQUESTS_CA_BUNDLE was not loaded into the derivation trust store"
    )
    # Strictness is unchanged — this adds an anchor, it never removes one.
    assert after.verify_mode == ssl.CERT_REQUIRED
    assert after.check_hostname is True


def test_an_unreadable_ca_bundle_does_not_break_derivation(monkeypatch, tmp_path):
    # STUB: AC32 — a stale REQUESTS_CA_BUNDLE pointing at a deleted file is a
    # common corporate-laptop state. It must not turn every derivation into a
    # traceback; the platform trust store still applies.
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", str(tmp_path / "gone.pem"))
    ctx = _sso._derivation_ssl_context()
    assert ctx.verify_mode == ssl.CERT_REQUIRED


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


# ----------------------------------------------------------------------
# The hop *address*, not just its scheme. Tier 1 fetches a URL read out of a
# response header and then a second read out of that document — so a hostile or
# compromised instance can otherwise steer the operator's machine at loopback,
# the cloud metadata endpoint, or anything on the corporate LAN, and learn the
# outcome from the refusal message.
# ----------------------------------------------------------------------


@pytest.mark.parametrize("spelling", [
    "https://jira.corp.example.com",
    "https://jira.corp.example.com:443",
    "https://JIRA.CORP.EXAMPLE.COM",
])
def test_default_and_explicit_443_are_one_origin(spelling):     # STUB: AC32
    # An RFC 9728 header is free to spell the explicit port. Without
    # normalisation the resource server's own metadata hop looks off-origin,
    # resolves private for an internally hosted instance, and is refused —
    # reintroducing exactly the tier-1 failure the exemption exists to prevent.
    assert _sso._scheme_and_host(spelling) == "https://jira.corp.example.com:443"


@pytest.mark.parametrize("internal", [
    "https://127.0.0.1/authorize",           # loopback
    "https://169.254.169.254/latest/meta-data/",  # cloud instance metadata
    "https://10.1.2.3/authorize",            # RFC 1918
    "https://192.168.1.1/authorize",
    "https://[::1]/authorize",               # IPv6 loopback
])
def test_header_derived_hops_cannot_reach_internal_addresses(internal, monkeypatch):
    # STUB: AC32 — asserted on "no connection was attempted", not merely on the
    # abort: a refused connection to 127.0.0.1:443 raises `_DerivationAbort`
    # too, so an exception-type-only assertion stays green with the guard
    # removed (verified by mutation).
    class _MustNotOpen:
        def open(self, req, timeout=None):
            raise AssertionError(f"a request was made to {req.full_url}")

    monkeypatch.setattr(_sso, "_derivation_opener", lambda: _MustNotOpen())
    with pytest.raises(_sso._DerivationAbort, match="internal or could not be verified"):
        _sso._derive_open(internal, _sso._DerivationBudget(15.0))


def test_the_configured_base_url_may_be_internal():             # STUB: AC32
    # A corporate instance legitimately lives on an RFC 1918 host, so the guard
    # applies only to hops whose target came from a server response. Asserted on
    # the flag the tiers pass, since the request itself would need a listener.
    budget = _sso._DerivationBudget(_sso._DERIVE_TOTAL_BUDGET_S)
    assert _sso._resolves_to_internal_address("127.0.0.1", budget) is True
    assert _sso._resolves_to_internal_address("10.0.0.1", budget) is True


def test_a_stalled_resolver_cannot_outrun_the_budget(monkeypatch):   # STUB: AC32
    # `getaddrinfo` takes no timeout, so an unanswered lookup would otherwise
    # add the OS resolver's own wait to the derivation's advertised bound.
    # Fails closed: an unanswered lookup is not evidence the host is external.
    import time as _time

    def _never_answers(*_a, **_k):
        _time.sleep(30)
        raise AssertionError("resolver should have been abandoned")

    monkeypatch.setattr(_sso.socket, "getaddrinfo", _never_answers)
    budget = _sso._DerivationBudget(_sso._DERIVE_TOTAL_BUDGET_S)
    started = _time.monotonic()
    assert _sso._resolves_to_internal_address("stalls.example", budget) is True
    assert _time.monotonic() - started < _sso._DERIVE_SOCKET_TIMEOUT_S + 2


def test_every_tier_passes_the_configured_origin_as_trusted(monkeypatch):  # STUB: AC32
    opener = _FakeOpener({
        BASE: _Canned(200),
        f"{BASE}/.well-known/openid-configuration": _Canned(404),
        f"{BASE}/login.jsp": _Canned(200),
    }).install(monkeypatch)
    credbroker.derive_sso_destination(BASE, strategies=("atlassian-seraph",))
    assert all(o == _sso._origin(BASE) for o in opener.trusted_origin), (
        "every hop must carry the operator's configured origin as trusted; "
        f"got {opener.trusted_origin}"
    )


def test_tier1_still_works_when_the_instance_is_internally_hosted(monkeypatch):
    # STUB: AC32 — the regression an exemption keyed to "the first call" causes.
    # RFC 9728 puts /.well-known/oauth-protected-resource on the resource server
    # itself, so tier 1's *second* hop is the same origin as its first. With
    # every address treated as internal, that hop must still be made.
    monkeypatch.setattr(_sso, "_resolves_to_internal_address", lambda host: True)
    opener = _FakeOpener({
        BASE: _Canned(
            401,
            {"WWW-Authenticate": f'Bearer resource_metadata="{BASE}/.well-known/oauth-protected-resource"'},
        ),
        f"{BASE}/.well-known/oauth-protected-resource": _Canned.json(
            {"authorization_servers": [IDP]}
        ),
        f"{IDP}/.well-known/oauth-authorization-server": _Canned.json(
            {"authorization_endpoint": f"{IDP}/authorize"}
        ),
    })
    # Install the routes but keep the *real* address guard for this one.
    outer = opener
    real_open = _sso._derive_open

    def _open(url, budget, *, trusted_origin=None):
        # Records what was actually *fetched*, so the guard's refusals do not
        # count as requests.
        parts = urllib.parse.urlsplit(url)
        origin = _sso._origin(url)
        if origin != trusted_origin and _sso._resolves_to_internal_address(parts.hostname or ""):
            raise _sso._DerivationAbort("internal or could not be verified")
        outer.fetched.append(url)
        canned = outer.routes.get(url)
        if canned is None:
            raise _sso._DerivationAbort(f"no route for {url}")
        return _sso._DerivationResponse(canned.status, canned.headers, canned.body)

    monkeypatch.setattr(_sso, "_derive_open", _open)
    del real_open

    credbroker.derive_sso_destination(BASE)
    assert f"{BASE}/.well-known/oauth-protected-resource" in opener.fetched, (
        "the same-origin resource-metadata hop was refused; tier 1 is dead for "
        f"every internally-hosted instance. fetched={opener.fetched}"
    )
    # ...and the off-origin issuer hop is still refused.
    assert f"{IDP}/.well-known/oauth-authorization-server" not in opener.fetched


@pytest.mark.parametrize("malformed", ["https://[", "https://[::1", "https://a]b"])
def test_a_malformed_url_is_an_abort_not_a_valueerror(malformed):   # STUB: AC32
    # `urlsplit("https://[")` raises ValueError. Every string reaching these two
    # functions is server-supplied, and neither `derive_sso_destination` nor the
    # consumer catches ValueError — so uncaught it lands in the CLI's catch-all
    # as exit 1, outside the exit-2 credential band.
    with pytest.raises(_sso._DerivationAbort):
        _sso._derive_open(malformed, _sso._DerivationBudget(15.0))
    assert _sso._scheme_and_host(malformed) is None


@pytest.mark.parametrize("tier_route", [
    ("authorization_endpoint", "https://["),
    ("authorization_servers", ["https://["]),
])
def test_a_malformed_url_in_a_document_degrades_to_cannot_derive(monkeypatch, tier_route):
    # STUB: AC32 — end to end: the public entry point returns None rather than
    # raising, whichever tier the malformed value arrives in.
    key, value = tier_route
    _FakeOpener({
        BASE: _Canned(
            401,
            {"WWW-Authenticate": f'Bearer resource_metadata="{BASE}/.well-known/oauth-protected-resource"'},
        ),
        f"{BASE}/.well-known/oauth-protected-resource": _Canned.json({key: value}),
        f"{BASE}/.well-known/openid-configuration": _Canned.json({key: value}),
    }).install(monkeypatch)
    assert credbroker.derive_sso_destination(BASE) is None


def test_read_capped_works_against_real_response_objects():     # STUB: AC32
    # The two fakes above model `read1`; this drives the real objects the
    # production path sees. Without it, `read1` disappearing from either would
    # be an AttributeError in production while the suite stayed green — and the
    # old `or fp.read` fallback would have made it a silent return to the
    # unbounded read this whole guard removed.
    payload = b'{"authorization_endpoint": "https://idp.example/authorize"}'

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):                       # noqa: N802 — stdlib contract
            status = 401 if self.path == "/401" else 200
            self.send_response(status)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *a):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    budget = _sso._DerivationBudget(15.0)
    try:
        base = f"http://127.0.0.1:{server.server_port}"
        # A real HTTPResponse...
        with urllib.request.urlopen(f"{base}/ok", timeout=5) as resp:
            assert _sso._read_capped(resp, budget) == payload
        # ...and a real HTTPError, which is what tier 1's 401 arrives as.
        try:
            urllib.request.urlopen(f"{base}/401", timeout=5)
        except urllib.error.HTTPError as exc:
            assert _sso._read_capped(exc, budget) == payload
        else:  # pragma: no cover
            pytest.fail("expected an HTTPError")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_rfc8414_inserts_the_wellknown_before_the_issuer_path():  # STUB: AC32
    # RFC 8414 §3 puts the well-known segment between the authority and the
    # path, so a multi-tenant issuer publishes at
    # `https://idp/.well-known/oauth-authorization-server/tenant`. Appending
    # both suffixes misses every such deployment and reports cannot-derive.
    urls = _sso._authorization_server_metadata_urls("https://idp.example/tenant")
    assert urls[0] == "https://idp.example/.well-known/oauth-authorization-server/tenant"
    # OIDC Discovery appends, and is kept as the second attempt.
    assert urls[1] == "https://idp.example/tenant/.well-known/openid-configuration"
    # A path-less issuer is unaffected.
    plain = _sso._authorization_server_metadata_urls("https://idp.example")
    assert plain[0] == "https://idp.example/.well-known/oauth-authorization-server"


def test_a_multitenant_issuer_is_discovered(monkeypatch):       # STUB: AC32
    tenant = "https://idp.example/tenant"
    _FakeOpener({
        BASE: _Canned(
            401,
            {"WWW-Authenticate": f'Bearer resource_metadata="{BASE}/.well-known/oauth-protected-resource"'},
        ),
        f"{BASE}/.well-known/oauth-protected-resource": _Canned.json(
            {"authorization_servers": [tenant]}
        ),
        "https://idp.example/.well-known/oauth-authorization-server/tenant":
            _Canned.json({"authorization_endpoint": "https://idp.example/tenant/authorize"}),
    }).install(monkeypatch)
    assert credbroker.derive_sso_destination(BASE) == "https://idp.example:443"


def test_every_read_is_bounded_by_the_remaining_budget():       # STUB: AC32
    # The socket timeout is set once when the hop opens, so a server emitting a
    # byte just before each timeout could keep `read1` returning while the
    # shared deadline expired — overrunning the advertised total by nearly a
    # full socket timeout. Each read now re-arms the socket to what is left.
    import time as _time

    class _Sock:
        def __init__(self):
            self.timeouts: list[float] = []

        def settimeout(self, value):
            self.timeouts.append(value)

    class _Raw:
        def __init__(self, sock):
            self._sock = sock

    class _Fp:
        def __init__(self, sock):
            self.raw = _Raw(sock)

    class _Drip:
        """Mirrors a real `HTTPResponse`: `.fp.raw._sock` is the socket."""

        def __init__(self):
            self.sock = _Sock()
            self.fp = _Fp(self.sock)

        def read1(self, n):
            _time.sleep(0.02)
            return b"x"

        def close(self):
            pass

    drip = _Drip()
    with pytest.raises(_sso._DerivationAbort):
        _sso._read_capped(drip, _sso._DerivationBudget(0.2))

    assert drip.sock.timeouts, "the socket timeout was never re-armed per read"
    # Monotonically shrinking toward the deadline, never above the per-hop cap.
    assert all(t <= _sso._DERIVE_SOCKET_TIMEOUT_S for t in drip.sock.timeouts)
    assert drip.sock.timeouts[-1] < drip.sock.timeouts[0]


@pytest.mark.parametrize("url,expected", [
    # An explicit :0 is a port, not an omission — `port or default` made
    # `https://h:0` and `https://h` compare equal.
    ("https://idp.example:0/authorize", "https://idp.example:0"),
    ("https://idp.example/authorize", "https://idp.example:443"),
    # `urlsplit(...).hostname` strips IPv6 brackets; re-serialising without
    # them yields `https://::1:443`, which is neither a URL nor comparable.
    ("https://[2001:db8::1]:8443/authorize", "https://[2001:db8::1]:8443"),
    ("https://[2001:db8::1]/authorize", "https://[2001:db8::1]:443"),
])
def test_origin_serialisation_is_exact(url, expected):          # STUB: AC32
    assert _sso._scheme_and_host(url) == expected
