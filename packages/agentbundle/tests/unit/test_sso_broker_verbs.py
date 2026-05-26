"""T5 (credential-broker-contract): sso-broker.py verb correctness and
invariants — AC9 / AC9b / AC10 / AC11 / AC12 / AC13 / AC14 / AC17.

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
import shutil
import subprocess
import sys
import types

import pytest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
BROKER_DIR = REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "adapter-root-bins"
BROKER_PY = BROKER_DIR / "sso-broker.py"
SHIM_DIR = REPO_ROOT / "packs" / "credential-brokers" / ".apm" / "shared-libs"


def _load_broker_module(home: pathlib.Path) -> types.ModuleType:
    """Load sso-broker.py against a sandboxed HOME so its module-level
    constants resolve under the test's tmp path."""
    # Stage the broker dir under home/.agentbundle/bin and rewrite
    # _AGENTBUNDLE_HOME via monkeypatch after import.
    spec = importlib.util.spec_from_file_location("sso_broker", BROKER_PY)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    # Make Tier-2 sibling helpers importable absolutely (the broker
    # file does this itself via sys.path.insert when relative import fails).
    sys.path.insert(0, str(BROKER_DIR))
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.path.remove(str(BROKER_DIR))
    return mod


@pytest.fixture
def broker(tmp_path, monkeypatch):
    """Load the broker, sandbox its HOME, and stub the Tier-2 backend
    to an in-memory dict so tests run cross-platform."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))

    mod = _load_broker_module(home)

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
# AC9b — byte-equivalence of bundled Tier-2 helpers (filename rename only).
# ----------------------------------------------------------------------


def test_ac9b_sso_keychain_macos_byte_equivalent_to_shim_sibling():
    """The broker's sibling _sso_keychain_macos.py is byte-equivalent
    to the shim's _keychain_macos.py (filename rename only)."""
    broker_helper = (BROKER_DIR / "_sso_keychain_macos.py").read_bytes()
    shim_helper = (SHIM_DIR / "_keychain_macos.py").read_bytes()
    assert broker_helper == shim_helper, (
        "T5 broker keychain helper diverged from shim sibling — AC9b violated"
    )


def test_ac9b_sso_credman_windows_byte_equivalent_to_shim_sibling():
    broker_helper = (BROKER_DIR / "_sso_credman_windows.py").read_bytes()
    shim_helper = (SHIM_DIR / "_credman_windows.py").read_bytes()
    assert broker_helper == shim_helper


# ----------------------------------------------------------------------
# AC9b — every write_credential / read_credential call constructs a
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
# AC12 — cookie-jar continuation when jar exceeds 2048 bytes.
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
# AC11 — Linux file-floor (no Tier-2 backend).
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
# AC13 — Playwright import-guard.
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
        pytest.skip("playwright IS installed in this test env; AC13 guard not exercised")
    assert res.returncode == 3
    assert "sso-broker: playwright not installed" in res.stderr
    assert "pip install playwright" in res.stderr
    assert "playwright install chromium" in res.stderr


# ----------------------------------------------------------------------
# AC14 — corporate-network env passthrough invariant.
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
# AC9 / AC10 — verb correctness.
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
# AC17 — canonical broker path (consumer-side resolution).
# ----------------------------------------------------------------------


def test_ac17_broker_lives_at_canonical_path():
    """The broker file is named sso-broker.py and is projected (by T6)
    to ~/.agentbundle/bin/. The source-of-truth path under packs/ is
    fixed; T6's projection test covers the materialised user-scope
    location."""
    assert BROKER_PY.is_file()
    assert BROKER_PY.name == "sso-broker.py"
    assert BROKER_PY.parent.name == "adapter-root-bins"
