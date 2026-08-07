"""T5 (credential-broker-contract): sso-broker.py verb correctness and
invariants.

These tests load the broker module from
``packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py`` via
``importlib`` (the file lives outside Python's package tree). Tier-2
helpers are loaded as siblings under a tmp-path so each test exercises
the broker against an isolated backend.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
import sys
import types

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
BROKER_DIR = REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "adapter-root-bins"
BROKER_PY = BROKER_DIR / "sso-broker.py"
# projected copy that `make build-self` places in .agentbundle/bin/
PROJECTED_BROKER_PY = REPO_ROOT / ".agentbundle" / "bin" / "sso-broker.py"
SHIM_DIR = REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "shared-libs"


def _load_cli_module(py_path: pathlib.Path) -> types.ModuleType:
    """Load a Python file as a module via importlib, prepending its parent
    to sys.path for the duration of the load.

    Generalises ``_load_broker_module``: uses ``py_path.parent`` as the
    sys.path prefix rather than a hardcoded directory, so both the pack-source
    and the projected (``.agentbundle/bin/``) copy can be loaded identically.
    """
    spec = importlib.util.spec_from_file_location(py_path.stem, py_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(py_path.parent))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(py_path.parent))
    return mod


@pytest.fixture(params=["source", "projected"])
def broker(request, tmp_path, monkeypatch):
    """Load the broker, sandbox its HOME, and stub the Tier-2 backend
    to an in-memory dict so tests run cross-platform. parametrised over two paths:
      - "source"   — pack-source ``packs/credential-brokers/.apm/adapter-root-bins/sso-broker.py``
      - "projected" — ``make build-self`` output at ``.agentbundle/bin/sso-broker.py``

    The "projected" variant skips when the projected file is absent (unbuilt
    checkout); both must pass when the projected file exists.
    """
    if request.param == "projected":
        broker_py = PROJECTED_BROKER_PY
        if not broker_py.is_file():
            pytest.skip(f"{broker_py} not present — run make build-self")
    else:
        broker_py = BROKER_PY

    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    mod = _load_cli_module(broker_py)

    # Rewrite the module-level paths to point under the sandboxed home.
    mod._AGENTBUNDLE_HOME = home / ".agentbundle"
    mod._SSO_PROFILE_DIR = mod._AGENTBUNDLE_HOME / "sso-profiles"
    mod._SSO_COOKIE_FILE_FLOOR = mod._AGENTBUNDLE_HOME / "sso-cookies"

    # Stub Tier-2 with an in-memory dict that tracks (namespace, key) → value.
    class _InMemoryBackend:
        def __init__(self):
            self.store: dict[tuple[str, str], str] = {}
            self.refuse_after = None  # set to int to simulate continuation refusal

        def write_credential(self, namespace, key, value):
            if self.refuse_after is not None and len(self.store) >= self.refuse_after:
                raise RuntimeError("simulated keychain capacity refusal")
            self.store[(namespace, key)] = value

        def read_credential(self, namespace, key):
            return self.store.get((namespace, key))

        def delete_credential(self, namespace, key):
            self.store.pop((namespace, key), None)

    backend = _InMemoryBackend()
    mod._tier2_backend = backend
    yield mod, backend


# ----------------------------------------------------------------------
# byte-equivalence of bundled Tier-2 helpers (filename rename only).
# ----------------------------------------------------------------------


def test_ac9b_sso_keychain_macos_byte_equivalent_to_shim_sibling():
    """The broker's sibling _sso_keychain_macos.py is byte-equivalent
    to the shim's _keychain_macos.py (filename rename only)."""
    broker_helper = (BROKER_DIR / "_sso_keychain_macos.py").read_bytes()
    shim_helper = (SHIM_DIR / "_keychain_macos.py").read_bytes()
    assert broker_helper == shim_helper, (
        "T5 broker keychain helper diverged from shim sibling — the contract violated"
    )


def test_ac9b_sso_credman_windows_byte_equivalent_to_shim_sibling():
    broker_helper = (BROKER_DIR / "_sso_credman_windows.py").read_bytes()
    shim_helper = (SHIM_DIR / "_credman_windows.py").read_bytes()
    assert broker_helper == shim_helper


# ----------------------------------------------------------------------
# every write_credential / read_credential call constructs a
# target name of shape agentbundle:sso:<profile>.
# ----------------------------------------------------------------------


def test_ac9b_target_name_namespace_is_agentbundle_sso(broker):
    mod, backend = broker
    assert mod._SSO_NAMESPACE == "agentbundle:sso"

    ns, key = mod._profile_target("acme")
    assert ns == "agentbundle:sso"
    assert key == "acme"

    ns, key = mod._profile_target("acme", chunk=2)
    assert ns == "agentbundle:sso"
    assert key == "acme:2"


def test_ac9b_write_credential_rejects_non_sso_namespace(broker):
    mod, _ = broker
    with pytest.raises(RuntimeError, match="non-sso namespace"):
        mod.write_credential("not-sso", "anything", "value")


# ----------------------------------------------------------------------
# cookie-jar continuation when jar exceeds 2048 bytes.
# ----------------------------------------------------------------------


def test_ac12_constant_is_2048(broker):
    mod, _ = broker
    assert mod.CRED_MAX_CREDENTIAL_BLOB_SIZE_BYTES == 2048


def test_ac12_small_jar_stored_in_single_credential(broker):
    mod, backend = broker
    payload = b'[{"name":"sid","value":"abc"}]'
    label = mod._store_cookie_jar("acme", payload)
    assert label == "keychain"
    assert (mod._SSO_NAMESPACE, "acme") in backend.store
    # Header is the raw jar, not a continuation-meta JSON.
    stored = backend.store[(mod._SSO_NAMESPACE, "acme")]
    assert stored == payload.decode("utf-8")


def test_ac12_large_jar_splits_into_continuation_credentials(broker):
    mod, backend = broker
    # 3 KB payload — exceeds the 2048 threshold; should split into 2 chunks.
    payload = ("x" * 3000).encode("utf-8")
    label = mod._store_cookie_jar("big", payload)
    assert label == "keychain-continuation"
    # Header at agentbundle:sso:big stores {"continuation_count": 2}
    header = backend.store[(mod._SSO_NAMESPACE, "big")]
    meta = json.loads(header)
    assert meta["continuation_count"] == 2
    # Two continuation slots at agentbundle:sso:big:0 and :1.
    assert (mod._SSO_NAMESPACE, "big:0") in backend.store
    assert (mod._SSO_NAMESPACE, "big:1") in backend.store


def test_ac12_overflow_to_file_when_backend_refuses_continuation(broker, monkeypatch):
    mod, backend = broker
    backend.refuse_after = 1  # accept header, refuse continuation slots
    payload = ("y" * 3000).encode("utf-8")
    label = mod._store_cookie_jar("overflow", payload)
    assert label == "file-floor-overflow"
    # File-floor jar exists.
    floor = mod._SSO_COOKIE_FILE_FLOOR / "overflow.jar"
    assert floor.is_file()
    assert floor.read_bytes() == payload


def test_ac12_jar_reassembly_from_continuation_credentials(broker):
    mod, _ = broker
    payload = ("z" * 3000).encode("utf-8")
    mod._store_cookie_jar("reass", payload)
    loaded = mod._load_cookie_jar("reass")
    assert loaded == payload


# ----------------------------------------------------------------------
# Linux file-floor (no Tier-2 backend).
# ----------------------------------------------------------------------


def test_ac11_linux_floors_to_file(broker, monkeypatch):
    mod, _ = broker
    # Simulate Linux: no Tier-2 backend.
    mod._tier2_backend = None
    payload = b'[{"name":"sid","value":"abc"}]'
    label = mod._store_cookie_jar("acme", payload)
    assert label == "file-floor"
    floor = mod._SSO_COOKIE_FILE_FLOOR / "acme.jar"
    assert floor.read_bytes() == payload


# ----------------------------------------------------------------------
# Playwright import-guard.
# ----------------------------------------------------------------------


def test_ac13_playwright_import_guard_exits_with_pinned_stderr(tmp_path, monkeypatch):
    """Invoke the broker with PYTHONPATH excluding playwright; assert
    pinned stderr."""
    env = {**os.environ, "PYTHONPATH": str(tmp_path), "HOME": str(tmp_path)}
    # Strip any inherited site-packages by isolating site.
    env["PYTHONNOUSERSITE"] = "1"
    res = subprocess.run(
        [sys.executable, "-S", str(BROKER_PY), "register", "test-profile",
         "--login-url", "http://example.com",
         "--success-url-pattern", "http://example.com/.*"],
        capture_output=True, text=True, env=env,
    )
    # If playwright isn't installed in the test environment, broker
    # exits 3 with the pinned stderr. If it IS installed, this test
    # is moot — skip.
    if "playwright not installed" not in res.stderr:
        pytest.skip("playwright IS installed in this test env; guard not exercised")
    assert res.returncode == 3
    assert "sso-broker: playwright not installed" in res.stderr
    assert "pip install playwright" in res.stderr
    assert "playwright install chromium" in res.stderr


# ----------------------------------------------------------------------
# corporate-network env passthrough invariant.
# ----------------------------------------------------------------------


def test_ac14_env_passthrough_in_register(broker, monkeypatch):
    """When the broker invokes playwright, the chromium.launch_persistent_context
    receives env={**os.environ, ...}; the test mocks launch_persistent_context
    and asserts the env kwarg shape against a fixture parent env."""
    mod, _ = broker

    # Fixture parent env carrying corporate-network proxy vars.
    monkeypatch.setenv("HTTPS_PROXY", "http://corp-proxy:8080")
    monkeypatch.setenv("NO_PROXY", "*.internal")
    monkeypatch.setenv("REQUESTS_CA_BUNDLE", "/etc/ssl/corp-ca.pem")

    captured: dict = {}

    class _FakeContext:
        pages: list = []

        def new_page(self):
            class _P:
                url = "http://example.com/success/landing"

                def goto(self, *a, **k): pass

                def wait_for_timeout(self, *a, **k): pass

            return _P()

        def cookies(self):
            return [{"name": "sid", "value": "v", "domain": "example.com"}]

        def close(self): pass

    class _FakeChromium:
        @staticmethod
        def launch_persistent_context(**kwargs):
            captured.update(kwargs)
            return _FakeContext()

    class _FakePw:
        chromium = _FakeChromium()

        def __enter__(self): return self

        def __exit__(self, *a): pass

    def _fake_import_playwright():
        return lambda: _FakePw()

    monkeypatch.setattr(mod, "_import_playwright", _fake_import_playwright)

    args = argparse_namespace(
        login_url="http://example.com/login",
        success_url_pattern="http://example.com/success/.*",
        cookie_domain=None,
        session_filename="",
        validation_endpoint="",
        ttl_hint_minutes=0,
    )
    rc = mod._do_register("acme", args)
    assert rc == 0, "register should succeed against the mocked Playwright"
    assert "env" in captured, "launch_persistent_context not called with env kwarg"
    forwarded = captured["env"]
    assert forwarded.get("HTTPS_PROXY") == "http://corp-proxy:8080"
    assert forwarded.get("NO_PROXY") == "*.internal"
    assert forwarded.get("REQUESTS_CA_BUNDLE") == "/etc/ssl/corp-ca.pem"


def argparse_namespace(**kwargs):
    import argparse as _ap
    return _ap.Namespace(**kwargs)


# ----------------------------------------------------------------------
# verb correctness.
# ----------------------------------------------------------------------


def test_ac10_register_writes_canonical_profile_toml(broker, monkeypatch):
    mod, _ = broker

    class _FakeContext:
        pages: list = []

        def new_page(self):
            class _P:
                url = "https://jira.acme.com/secure/dashboard"

                def goto(self, *a, **k): pass
                def wait_for_timeout(self, *a, **k): pass
            return _P()

        def cookies(self):
            return [
                {"name": "JSESSIONID", "value": "abc", "domain": ".jira.acme.com"},
                {"name": "OAUTH_TOKEN", "value": "xyz", "domain": "sso.acme.com"},
            ]

        def close(self): pass

    class _FakeChromium:
        @staticmethod
        def launch_persistent_context(**kwargs):
            return _FakeContext()

    class _FakePw:
        chromium = _FakeChromium()

        def __enter__(self): return self
        def __exit__(self, *a): pass

    monkeypatch.setattr(mod, "_import_playwright", lambda: lambda: _FakePw())

    args = argparse_namespace(
        login_url="https://jira.acme.com",
        success_url_pattern="https://jira.acme.com/secure/.*",
        cookie_domain=None,
        session_filename="",
        validation_endpoint="/rest/api/2/myself",
        ttl_hint_minutes=480,
    )
    rc = mod._do_register("acme-jira", args)
    assert rc == 0
    toml_path = mod._SSO_PROFILE_DIR / "acme-jira.toml"
    assert toml_path.is_file()
    import tomllib as _tomllib
    with toml_path.open("rb") as fh:
        body = _tomllib.load(fh)
    table = body["profile"]
    assert table["name"] == "acme-jira"
    assert table["login_url"] == "https://jira.acme.com"
    assert table["success_url_pattern"] == "https://jira.acme.com/secure/.*"
    assert "jira.acme.com" in table["cookie_domains"]
    assert "sso.acme.com" in table["cookie_domains"]
    assert table["validation_endpoint"] == "/rest/api/2/myself"
    assert table["ttl_hint_minutes"] == 480


def test_ac9_get_cookies_emits_path_not_value(broker, monkeypatch):
    mod, _ = broker
    # Set up a profile + jar by hand.
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    mod._write_profile("p1", {
        "name": "p1", "login_url": "x", "success_url_pattern": "x",
        "cookie_domains": ["x"], "session_filename": "x",
        "validation_endpoint": "/v", "ttl_hint_minutes": 10,
    })
    jar = b'[{"name":"sid","value":"SECRET-NOT-PRINTED","domain":"x"}]'
    mod._store_cookie_jar("p1", jar)

    # Capture stdout via redirect.
    import io
    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    rc = mod._do_get_cookies("p1")
    assert rc == 0
    out = buf.getvalue()
    assert "SECRET-NOT-PRINTED" not in out
    # The emitted line is the cookie-jar file path.
    expected = mod._SSO_COOKIE_FILE_FLOOR / "p1.jar"
    assert out.strip() == str(expected)


def test_ac9_get_cookies_missing_profile_returns_2(broker):
    mod, _ = broker
    rc = mod._do_get_cookies("nonexistent")
    assert rc == 2


def test_ac9_get_cookies_missing_jar_returns_2(broker):
    mod, _ = broker
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    mod._write_profile("p2", {
        "name": "p2", "login_url": "x", "success_url_pattern": "x",
        "cookie_domains": ["x"], "session_filename": "x",
        "validation_endpoint": "/v", "ttl_hint_minutes": 10,
    })
    rc = mod._do_get_cookies("p2")
    assert rc == 2


def test_ac9_rm_removes_profile_and_jar(broker):
    mod, _ = broker
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    mod._write_profile("p3", {
        "name": "p3", "login_url": "x", "success_url_pattern": "x",
        "cookie_domains": ["x"], "session_filename": "x",
        "validation_endpoint": "/v", "ttl_hint_minutes": 10,
    })
    mod._store_cookie_jar("p3", b'[{"name":"sid","value":"v","domain":"x"}]')

    rc = mod._do_rm("p3")
    assert rc == 0
    assert not (mod._SSO_PROFILE_DIR / "p3.toml").exists()
    assert mod._load_cookie_jar("p3") is None


def test_ac9_list_profiles_lists_registered(broker, monkeypatch):
    mod, _ = broker
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    for name in ("alpha", "beta"):
        mod._write_profile(name, {
            "name": name, "login_url": "x", "success_url_pattern": "x",
            "cookie_domains": ["x"], "session_filename": "x",
            "validation_endpoint": "/v", "ttl_hint_minutes": 10,
        })
    mod._store_cookie_jar("alpha", b'[]')

    import io
    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    rc = mod._do_list_profiles()
    assert rc == 0
    out = buf.getvalue()
    assert "alpha\tvalid" in out
    assert "beta\tno-jar" in out


# ----------------------------------------------------------------------
# canonical broker path (consumer-side resolution).
# ----------------------------------------------------------------------


def test_ac17_broker_lives_at_canonical_path():
    """The broker file is named sso-broker.py and is projected (by T6)
    to ~/.agentbundle/bin/. The source-of-truth path under packs/ is
    fixed; T6's projection test covers the materialised user-scope
    location."""
    assert BROKER_PY.is_file()
    assert BROKER_PY.name == "sso-broker.py"
    assert BROKER_PY.parent.name == "adapter-root-bins"


# ----------------------------------------------------------------------
# Windows cp1252 console hardening.
# ----------------------------------------------------------------------


def test_stdio_utf8_hardening_present() -> None:
    """Source-asserted (not behavioral): reproducing a cp1252 console is not
    portable, but the structure — reconfigure inside the file-path-invocation
    gate, before any output — is verifiable from source bytes."""
    src = BROKER_PY.read_text(encoding="utf-8")
    assert 'reconfigure(encoding="utf-8")' in src, (
        "stdout/stderr UTF-8 hardening missing from sso-broker.py"
    )
    gate_pos = src.index('if __package__ in (None, "") and __spec__ is None:')
    reconfigure_pos = src.index('reconfigure(encoding="utf-8")')
    assert gate_pos < reconfigure_pos, (
        "UTF-8 hardening must sit inside the file-path-invocation gate"
    )


# ----------------------------------------------------------------------
# URL scheme allowlist on `test` (B310 / SSRF-adjacent hardening).
# ----------------------------------------------------------------------


def test_do_test_rejects_non_http_url_scheme(broker):
    """`_do_test` refuses a profile whose resolved URL scheme is not
    http(s): a file:// login_url (e.g. a corrupt or hand-edited profile)
    returns exit 3 *before* urllib.urlopen, closing the file:// local-read
    vector rather than suppressing the Bandit B310 finding blindly."""
    mod, _ = broker
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    mod._profile_path("evil").write_text(
        '[profile]\nlogin_url = "file:///etc/passwd"\nvalidation_endpoint = "/x"\n',
        encoding="utf-8",
    )
    # A cookie jar must exist so _do_test reaches the scheme check.
    mod._store_cookie_jar("evil", b'[{"name":"sid","value":"v"}]')
    assert mod._do_test("evil") == 3


def test_do_test_accepts_https_url_scheme(broker, monkeypatch):
    """The guard does not reject legitimate https endpoints: with the
    network call stubbed to a 2xx, a normal https profile returns 0."""
    mod, _ = broker
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    mod._profile_path("acme").write_text(
        '[profile]\nlogin_url = "https://acme.example.com"\nvalidation_endpoint = "/whoami"\n',
        encoding="utf-8",
    )
    mod._store_cookie_jar("acme", b'[{"name":"sid","value":"v"}]')

    class _Resp:
        status = 200

        def __enter__(self): return self
        def __exit__(self, *a): pass

    monkeypatch.setattr(mod.urllib.request, "urlopen", lambda *a, **k: _Resp())
    assert mod._do_test("acme") == 0


def test_do_test_rejects_schemeless_url(broker):
    """A schemeless login_url (degenerate / hand-edited profile) resolves to an
    empty url scheme, which the allowlist also rejects (exit 3) — the guard
    fails closed rather than letting a protocol-relative value through."""
    mod, _ = broker
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    mod._profile_path("bare").write_text(
        '[profile]\nlogin_url = "acme.example.com"\nvalidation_endpoint = "//evil.example/x"\n',
        encoding="utf-8",
    )
    mod._store_cookie_jar("bare", b'[{"name":"sid","value":"v"}]')
    assert mod._do_test("bare") == 3


# ----------------------------------------------------------------------
# AC6a / AC6b — the refreshed jar reaches the consumer, and "not registered"
# has its own exit code.
# ----------------------------------------------------------------------


def _seed_profile(mod, profile: str) -> None:
    """Write a minimal valid profile TOML for *profile*."""
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    mod._write_profile(profile, {
        "name": profile,
        "login_url": "https://jira.example.com/login",
        "success_url_pattern": "https://jira.example.com/secure/.*",
        "cookie_domains": ["jira.example.com"],
        "session_filename": f"{profile}-session.jar",
        "validation_endpoint": "/rest/api/2/myself",
        "ttl_hint_minutes": 480,
    })


def _get_cookies_path(mod, monkeypatch, profile: str) -> pathlib.Path:
    """Run ``get-cookies`` and return the materialised path it printed."""
    import io
    buf = io.StringIO()
    monkeypatch.setattr(sys, "stdout", buf)
    rc = mod._do_get_cookies(profile)
    assert rc == 0, f"get-cookies returned {rc}"
    return pathlib.Path(buf.getvalue().strip())


@pytest.fixture(params=["keychain", "file-floor"])
def store_backend(request, broker):
    """Run a test under both store shapes.

    The keychain arm is the AC6a regression guard: there the primary store and
    the materialisation surface are *different* files, so a materialisation that
    skips the rewrite serves a stale jar after every re-capture. The file-floor
    arm is the control — the two are the same file there, which is why CI (Linux)
    never caught the bug.
    """
    mod, backend = broker
    if request.param == "file-floor":
        mod._tier2_backend = None
    return mod


def test_get_cookies_rewrites_stale_materialised_jar(store_backend, monkeypatch):  # STUB: AC6a
    mod = store_backend
    _seed_profile(mod, "jira")

    mod._store_cookie_jar("jira", b'[{"name":"old","value":"v","domain":"x"}]')
    p1 = _get_cookies_path(mod, monkeypatch, "jira")
    mod._store_cookie_jar("jira", b'[{"name":"new","value":"v","domain":"x"}]')
    p2 = _get_cookies_path(mod, monkeypatch, "jira")

    assert p1 == p2                            # same path…
    assert b"new" in p2.read_bytes()           # …fresh bytes (fails today)
    assert b"old" not in p2.read_bytes()


def test_write_uses_unique_temp_name(broker, monkeypatch):       # STUB: AC6a
    # Making the materialisation unconditional makes the shared temp path
    # routine: every check now rewrites, so two concurrent checks for one
    # profile collide on `<profile>.jar.tmp`. A unique name per write removes
    # the collision. (Ordering between concurrent materialisers is deliberately
    # unspecified — see AC6a and `sso-materialisation-ordering`.)
    mod, _ = broker
    seen: list[str] = []
    real_replace = pathlib.Path.replace

    def _record(self, target):
        seen.append(self.name)
        return real_replace(self, target)

    monkeypatch.setattr(pathlib.Path, "replace", _record)
    mod._file_floor_write("jira", b"[]")
    mod._file_floor_write("jira", b"[]")

    assert len(seen) == 2
    assert seen[0] != seen[1], f"temp name reused across writes: {seen}"
    assert all(name != "jira.jar" for name in seen)
    # No temp file survives either write.
    leftovers = sorted(p.name for p in mod._SSO_COOKIE_FILE_FLOOR.glob("*.tmp*"))
    assert leftovers == [], leftovers


def test_refresh_unregistered_returns_4(broker):                 # STUB: AC6b
    # `3` is returned from ten distinct engine sites — including playwright
    # being absent and the operator not finishing sign-in — so it cannot mean
    # "not registered". Recovery needs a code it can key on.
    mod, _ = broker
    assert mod.main(["refresh", "never-registered"]) == 4


# ----------------------------------------------------------------------
# AC6 / AC7 / AC8 / AC9 — the engine's own profile guard and path containment.
# ----------------------------------------------------------------------

_BAD_PROFILES = [
    "../../../../tmp/pwn", "abc\n", "abc\r\n", "x" * 65, "café",
    "", ".", "..", "CON", "con.toml",
]


@pytest.mark.parametrize("verb", ["register", "get-cookies", "test", "refresh"])
@pytest.mark.parametrize("bad", _BAD_PROFILES)
def test_profile_rejected_per_verb(broker, verb, bad, capsys):   # STUB: AC6/AC9
    mod, _ = broker
    assert mod.main([verb, bad]) == 3
    # The exit code alone is already green today for most of these vectors —
    # get-cookies and test return 2 for an unregistered profile, and register
    # returns 3 before mkdir when --login-url is absent — so the stderr
    # assertion is what makes this a red stub.
    err = capsys.readouterr().err.lower()
    assert "profile" in err
    assert "must match" in err or "reserved device name" in err


def test_profile_guard_precedes_path_composition(broker):        # STUB: AC6
    # The guard fires before any store path is composed, so a traversal vector
    # cannot create a directory outside the store.
    mod, _ = broker
    assert mod.main(["register", "../../../../tmp/pwn",
                     "--login-url", "https://idp.example",
                     "--success-url-pattern", "https://x.example/ok"]) == 3
    assert not (mod._AGENTBUNDLE_HOME / "browser-state").exists()


def test_flag_shaped_via_double_dash_reaches_guard(broker):      # STUB: AC9
    mod, _ = broker
    # The `--` escape parses -x as the positional, so the grammar's
    # leading-'-' rejection is load-bearing rather than cosmetic.
    assert mod.main(["get-cookies", "--", "-x"]) == 3


def test_bare_flag_is_argparse_exit(broker):                     # STUB: AC9
    mod, _ = broker
    with pytest.raises(SystemExit) as e:
        mod.main(["get-cookies", "-x"])
    assert e.value.code == 2


def test_non_str_profile_is_refused_not_a_traceback(broker):     # STUB: AC9
    # Reachable only in-process (argv is always str), but a non-str must fail
    # closed at the path composer rather than composing "5.jar".
    mod, _ = broker
    with pytest.raises(mod.ProfileConfinementError):
        mod._cookie_floor_path(5)


def test_path_containment_is_asserted_independently_of_grammar(broker):  # STUB: AC7
    # Grammar is a denylist of shapes; containment is an allowlist of
    # locations. Proven by driving the composer directly, past the verb guard.
    mod, _ = broker
    for bad in ("../escape", "sub/dir", "a\\b" if os.name == "nt" else "/abs"):
        with pytest.raises(mod.ProfileConfinementError):
            mod._profile_path(bad)
        with pytest.raises(mod.ProfileConfinementError):
            mod._cookie_floor_path(bad)


def test_rm_still_deletes_legacy_invalid_name(broker):           # STUB: AC8
    # A profile registered before this change under a now-invalid name must
    # remain deletable: list-profiles enumerates the filesystem directly and
    # would otherwise keep showing a live corporate cookie jar the operator
    # cannot remove.
    mod, _ = broker
    _seed_profile(mod, "legacy name")
    mod._store_cookie_jar("legacy name", b'[{"name":"sid","value":"v","domain":"x"}]')
    mod._file_floor_write("legacy name", b'[{"name":"sid","value":"v","domain":"x"}]')

    assert mod.main(["rm", "legacy name"]) == 0
    assert not mod._profile_path("legacy name").exists()
    assert not mod._cookie_floor_path("legacy name").exists()
    assert mod._load_cookie_jar("legacy name") is None


def test_rm_still_refuses_a_path_escape(broker):                 # STUB: AC7/AC8
    mod, _ = broker
    assert mod.main(["rm", "../../../../tmp/pwn"]) == 3


@pytest.mark.parametrize(
    "bad", ['a"b', "a" + chr(92) + "b", "a" + chr(1) + "b", "a" + chr(0x7F) + "b"]
)
@pytest.mark.parametrize("field", ["login_url", "cookie_domains"])  # scalar AND list
def test_write_profile_survives_toml_breaking_chars(broker, bad, field):  # STUB: AC6
    # `_write_profile` interpolates f'{key} = "{value}"' unescaped, and
    # `_do_refresh` reads the stored table then re-writes every value back
    # through it — so a consumer-side guard on *newly supplied* values does not
    # cover a profile poisoned before this change. A four-character check is not
    # enough either: a TOML source can encode U+0001 as an escape, so the parsed
    # value holds a bare control character with no literal backslash, passes a
    # quote/backslash/CR/LF check, and is interpolated straight back in.
    mod, _ = broker
    table = {
        "name": "p",
        "login_url": "https://idp.example",
        "success_url_pattern": "https://x.example/ok",
        "cookie_domains": ["x.example"],
        "session_filename": "p.jar",
        "validation_endpoint": "/v",
        "ttl_hint_minutes": 480,
    }
    table[field] = [bad] if field == "cookie_domains" else bad
    mod._write_profile("p", table)

    # What must hold is that the profile still round-trips through tomllib, so
    # every later check / refresh / rm can read it.
    import tomllib as _tomllib
    with mod._profile_path("p").open("rb") as fh:
        parsed = _tomllib.load(fh)["profile"]
    got = parsed[field][0] if field == "cookie_domains" else parsed[field]
    assert got == bad


# ----------------------------------------------------------------------
# AC35 / AC14a — the capture split: ephemeral vs persistent, headed vs
# headless, and `refresh`'s refusal to accept a destination.
# ----------------------------------------------------------------------


class _RecordedLaunch:
    """One `chromium.launch*` call, flattened for assertion."""

    def __init__(self, kind, kwargs):
        self.kind = kind                       # "persistent" | "ephemeral"
        self.kwargs = kwargs
        self.headless = kwargs.get("headless")
        self.user_data_dir = kwargs.get("user_data_dir", "")
        self.add_cookies_called = False
        self.goto_urls: list[str] = []


class _PlaywrightRecorder:
    """Records every launch the engine makes, and drives the URL the page
    reports so a test can choose whether the success pattern ever matches."""

    def __init__(self, landing_urls):
        # One URL per poll tick; the last value repeats forever.
        self._landing = list(landing_urls)
        self.launches: list[_RecordedLaunch] = []

    # -- assertion helpers ------------------------------------------------
    @property
    def capture(self):
        return self.launches[0]

    @property
    def seed(self):
        return self.launches[1]

    # -- fake playwright --------------------------------------------------
    def install(self, mod, monkeypatch):
        recorder = self

        class _Page:
            def __init__(self):
                self._tick = 0

            @property
            def url(self):
                idx = min(self._tick, len(recorder._landing) - 1)
                return recorder._landing[idx]

            def goto(self, url, *a, **k):
                recorder.launches[-1].goto_urls.append(url)

            def wait_for_timeout(self, *a, **k):
                self._tick += 1

        class _Context:
            pages: list = []

            def __init__(self, record):
                self._record = record
                self.closed = False

            def new_page(self):
                return _Page()

            def cookies(self):
                return [{"name": "sid", "value": "v", "domain": "jira.example.com"}]

            def storage_state(self):
                return {"cookies": self.cookies(), "origins": []}

            def add_cookies(self, cookies):
                self._record.add_cookies_called = True

            def close(self):
                self.closed = True

        class _Browser:
            def __init__(self, record):
                self._record = record
                self.closed = False

            def new_context(self, **kwargs):
                return _Context(self._record)

            def close(self):
                self.closed = True

        class _Chromium:
            @staticmethod
            def launch_persistent_context(**kwargs):
                rec = _RecordedLaunch("persistent", kwargs)
                recorder.launches.append(rec)
                return _Context(rec)

            @staticmethod
            def launch(**kwargs):
                rec = _RecordedLaunch("ephemeral", kwargs)
                recorder.launches.append(rec)
                return _Browser(rec)

        class _Pw:
            chromium = _Chromium()

            def __enter__(self):
                return self

            def __exit__(self, *a):
                pass

        monkeypatch.setattr(mod, "_import_playwright", lambda: lambda: _Pw())
        return self


_SUCCESS_URL = "https://jira.example.com/secure/Dashboard.jspa"
_LOGIN_URL = "https://idp.example.com/authorize?state=abc"


def _register_argv(profile="jira", *extra):
    return [
        "register", profile,
        "--login-url", "https://idp.example.com/login",
        "--success-url-pattern", r"https://jira\.example\.com/secure/.*",
        "--cookie-domain", "jira.example.com",
        "--validation-endpoint", "/rest/api/2/myself",
        *extra,
    ]


def test_register_capture_is_ephemeral_then_seeds(broker, monkeypatch):   # STUB: AC35
    mod, _ = broker
    calls = _PlaywrightRecorder([_SUCCESS_URL]).install(mod, monkeypatch)

    assert mod.main(_register_argv("jira", "--ephemeral")) == 0

    # Capture must NOT use the persistent profile...
    assert calls.capture.kind == "ephemeral"
    assert calls.capture.headless is False        # interactive capture is HEADED
    # ...but a second, headless persistent launch must seed it, so asserting
    # launch_persistent_context is never called would reject a correct
    # implementation.
    assert calls.seed.kind == "persistent" and calls.seed.headless is True
    assert calls.seed.user_data_dir.replace("\\", "/").endswith("browser-state/jira")
    assert calls.seed.add_cookies_called


@pytest.mark.parametrize("argv,kind,headless", [
    (["register", "jira"], "persistent", False),               # operator default
    (["register", "jira", "--ephemeral"], "ephemeral", False),  # register_sso_session
    (["refresh", "jira"], "persistent", True),                  # AC14a
])
def test_capture_mode_matrix(broker, monkeypatch, argv, kind, headless):   # STUB: AC35
    mod, _ = broker
    if argv[0] == "refresh":
        _seed_profile(mod, "jira")
        full = argv
    else:
        full = _register_argv(*argv[1:])
    calls = _PlaywrightRecorder([_SUCCESS_URL]).install(mod, monkeypatch)

    assert mod.main(full) == 0
    assert calls.capture.kind == kind
    assert calls.capture.headless is headless
    # Only the ephemeral capture needs a seeding launch behind it.
    assert (len(calls.launches) == 2) is (kind == "ephemeral")


def test_refresh_silent_redirect_within_window_succeeds(broker, monkeypatch):  # STUB: AC14a
    # A warm IdP session still redirects asynchronously: a zero-wait launch
    # would fail flows that would have succeeded.
    mod, _ = broker
    _seed_profile(mod, "jira")
    calls = _PlaywrightRecorder([_LOGIN_URL, _LOGIN_URL, _SUCCESS_URL]).install(
        mod, monkeypatch
    )
    assert mod.main(["refresh", "jira"]) == 0
    assert calls.capture.headless is True


def test_refresh_login_page_returns_5_and_closes(broker, monkeypatch, capsys):  # STUB: AC14a
    # The success pattern never matches: a human would be needed, so the engine
    # fails fast with its own exit code rather than leaving a page on screen.
    mod, _ = broker
    _seed_profile(mod, "jira")
    monkeypatch.setattr(mod, "_REFRESH_SILENT_WINDOW_S", 0.2)
    calls = _PlaywrightRecorder([_LOGIN_URL]).install(mod, monkeypatch)

    assert mod.main(["refresh", "jira"]) == 5
    assert "sign in" in capsys.readouterr().err.lower()
    assert len(calls.launches) == 1, "no second browser may be opened"


def test_refresh_never_polls_for_a_human(broker):                # STUB: AC14a
    # Pinned exactly, not banded: credbroker's 180 s refresh bound is *derived*
    # from this 20 s window, so a silent widening here would leave the spawn
    # timeout under-sized. The headed register poll is the only human-duration
    # wait in the engine.
    mod, _ = broker
    assert mod._REFRESH_SILENT_WINDOW_S == 20
    assert mod._REGISTER_SIGNIN_POLL_S == 300


@pytest.mark.parametrize("flag,value", [
    ("--login-url", "https://evil.example"),
    ("--success-url-pattern", "https://evil.example/.*"),
    ("--cookie-domain", "evil.example"),
    ("--validation-endpoint", "/x"),
    ("--session-filename", "x.jar"),
    ("--ttl-hint-minutes", "5"),
])
def test_refresh_rejects_every_connection_argument(broker, flag, value):   # STUB: AC35
    # Destinations come only from the stored profile. Without this, AC1's
    # "enforced by the signature" holds at the library layer only.
    mod, _ = broker
    _seed_profile(mod, "jira")
    assert mod.main(["refresh", "jira", flag, value]) == 3


def test_refresh_reads_the_destination_from_the_stored_profile(broker, monkeypatch):  # STUB: AC35
    mod, _ = broker
    _seed_profile(mod, "jira")
    calls = _PlaywrightRecorder([_SUCCESS_URL]).install(mod, monkeypatch)
    assert mod.main(["refresh", "jira"]) == 0
    assert calls.capture.goto_urls == ["https://jira.example.com/login"]


def test_browser_state_dir_is_contained(broker):                  # STUB: AC7
    mod, _ = broker
    with pytest.raises(mod.ProfileConfinementError):
        mod._browser_state_dir("../escape")


# ----------------------------------------------------------------------
# Failure paths that used to escape as a traceback and exit 1, on stdio the
# consumer inherits.
# ----------------------------------------------------------------------


def _fail_seed(mod, monkeypatch, where):
    """Make the seeding launch or its add_cookies raise."""
    calls = _PlaywrightRecorder([_SUCCESS_URL])
    calls.install(mod, monkeypatch)
    real = mod._seed_persistent_profile

    def _boom(pw, profile, storage_state, env):
        if where == "launch":
            class _Pw:
                class chromium:
                    @staticmethod
                    def launch_persistent_context(**kw):
                        raise RuntimeError("profile locked")
            return real(_Pw(), profile, storage_state, env)

        class _Ctx:
            def add_cookies(self, cookies):
                raise RuntimeError("write refused")

            def close(self):
                pass

        class _Pw2:
            class chromium:
                @staticmethod
                def launch_persistent_context(**kw):
                    return _Ctx()
        return real(_Pw2(), profile, storage_state, env)

    monkeypatch.setattr(mod, "_seed_persistent_profile", _boom)
    return calls


@pytest.mark.parametrize("where", ["launch", "add_cookies"])
def test_a_failed_seed_does_not_discard_the_capture(broker, monkeypatch, where, capsys):
    # STUB: AC35 — seeding runs *before* the profile TOML and the jar are
    # stored, so anything escaping it throws away a sign-in the human has
    # already completed. The docstring promises the opposite.
    mod, _ = broker
    _fail_seed(mod, monkeypatch, where)

    assert mod.main(_register_argv("jira", "--ephemeral")) == 0
    assert mod._profile_path("jira").exists(), "the capture was discarded"
    assert mod._load_cookie_jar("jira") is not None
    assert "re-register" in capsys.readouterr().err


@pytest.mark.parametrize("verb,expected", [
    ("get-cookies", 2), ("test", 2), ("refresh", 4),
])
def test_an_unreadable_profile_is_a_coded_exit(broker, verb, expected):
    # STUB: AC6 — `_load_profile` can raise TOMLDecodeError or ValueError, not
    # just FileNotFoundError. Uncaught those are a traceback and exit 1.
    mod, _ = broker
    mod._SSO_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    mod._profile_path("broken").write_text('[profile\nname = "broken', encoding="utf-8")
    assert mod.main([verb, "broken"]) == expected


def test_the_jar_temp_file_is_never_world_readable(broker, monkeypatch):
    # STUB: AC6a — `write_bytes` creates at the umask default and chmods after,
    # leaving the jar readable for the length of the write. That window used to
    # open once per profile; the unconditional rewrite opens it every call.
    mod, _ = broker
    seen: list[int] = []
    real_open = os.open

    def _record(path, flags, mode=0o777, *a, **k):
        if str(path).endswith(".tmp"):
            seen.append(mode)
        return real_open(path, flags, mode, *a, **k)

    monkeypatch.setattr(os, "open", _record)
    mod._file_floor_write("jira", b"[]")
    assert seen and all(m == 0o600 for m in seen), seen
    if os.name == "posix":
        assert (mod._SSO_COOKIE_FILE_FLOOR / "jira.jar").stat().st_mode & 0o077 == 0


def test_an_ephemeral_headless_capture_is_refused(broker):
    # STUB: AC35 — the fourth combination of the two booleans. It would seed a
    # standing profile from a session no human established.
    mod, _ = broker
    args = argparse_namespace(
        login_url="https://idp.example", success_url_pattern="https://x/ok",
        cookie_domain=None, session_filename="", validation_endpoint="",
        ttl_hint_minutes=0, ephemeral=True,
    )
    with pytest.raises(AssertionError, match="never headless"):
        mod._capture("jira", args, persist=False, headless=True)
