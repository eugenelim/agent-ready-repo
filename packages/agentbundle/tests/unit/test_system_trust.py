"""Tests for corporate trust-store resolution — spec/catalogue-corporate-trust-store.

Coverage:
  T1 — resolve_trust_paths precedence, build_context strictness + augment-not-replace
  T2 — macOS administrator keychain export, platform gating, runner failure modes

No real network calls. No assertion depends on this machine's keychain contents,
so the suite is machine-independent and no employer-identifying string can enter
a fixture (AGENTS.md § Privacy).
"""

from __future__ import annotations

import ssl
import sys
from pathlib import Path

import pytest
from agentbundle import system_trust
from agentbundle.catalogue import CatalogueError


def _real_pem(tmp_path, name="anchor.pem"):
    """Write a single real CA certificate lifted from the default store.

    Generating an X.509 cert needs a dependency this package refuses, so a
    genuine anchor is borrowed from the interpreter's own trust store instead.
    """
    ders = ssl.create_default_context().get_ca_certs(binary_form=True)
    if not ders:
        pytest.skip("interpreter has an empty default trust store")
    path = tmp_path / name
    path.write_text(ssl.DER_cert_to_PEM_cert(ders[0]))
    return path


# ---------------------------------------------------------------------------
# T1 — resolve_trust_paths precedence
# ---------------------------------------------------------------------------


def test_agentbundle_ca_bundle_wins_over_both_openssl_vars(tmp_path):
    ours = _real_pem(tmp_path, "ours.pem")
    theirs = _real_pem(tmp_path, "theirs.pem")
    cafile, _ = system_trust.resolve_trust_paths(
        {
            "AGENTBUNDLE_CA_BUNDLE": str(ours),
            "SSL_CERT_FILE": str(theirs),
            "REQUESTS_CA_BUNDLE": str(theirs),
        }
    )
    assert cafile == str(ours)


def test_ssl_cert_file_wins_over_requests_ca_bundle(tmp_path):
    """Matches credbroker/_sso.py: native OpenSSL env beats the mapped one."""
    native = _real_pem(tmp_path, "native.pem")
    mapped = _real_pem(tmp_path, "mapped.pem")
    cafile, _ = system_trust.resolve_trust_paths(
        {"SSL_CERT_FILE": str(native), "REQUESTS_CA_BUNDLE": str(mapped)}
    )
    assert cafile == str(native)


def test_requests_ca_bundle_used_when_it_is_the_only_one(tmp_path):
    mapped = _real_pem(tmp_path, "mapped.pem")
    cafile, _ = system_trust.resolve_trust_paths({"REQUESTS_CA_BUNDLE": str(mapped)})
    assert cafile == str(mapped)


def test_ssl_cert_dir_is_independent_of_file_precedence(tmp_path):
    ours = _real_pem(tmp_path, "ours.pem")
    capath_dir = tmp_path / "certs"
    capath_dir.mkdir()
    cafile, capath = system_trust.resolve_trust_paths(
        {"AGENTBUNDLE_CA_BUNDLE": str(ours), "SSL_CERT_DIR": str(capath_dir)}
    )
    assert cafile == str(ours)
    assert capath == str(capath_dir)


def test_all_unset_resolves_to_no_paths():
    assert system_trust.resolve_trust_paths({}) == (None, None)


def test_missing_agentbundle_ca_bundle_raises_naming_the_path(tmp_path):
    """Ours is set by hand for this feature, so a typo is reported, not absorbed."""
    ghost = tmp_path / "nope.pem"
    with pytest.raises(CatalogueError) as exc:
        system_trust.resolve_trust_paths({"AGENTBUNDLE_CA_BUNDLE": str(ghost)})
    assert str(ghost) in str(exc.value)


@pytest.mark.parametrize("var", ["SSL_CERT_FILE", "REQUESTS_CA_BUNDLE"])
def test_missing_inherited_var_does_not_raise(tmp_path, var):
    """A fleet-wide stale value must not harden into an install failure."""
    ctx = system_trust.build_context({var: str(tmp_path / "gone.pem")})
    assert ctx.verify_mode is ssl.CERT_REQUIRED


# ---------------------------------------------------------------------------
# T1 — build_context strictness and augment-not-replace
# ---------------------------------------------------------------------------


def test_context_is_strict_with_no_env():
    ctx = system_trust.build_context({})
    assert ctx.check_hostname is True
    assert ctx.verify_mode is ssl.CERT_REQUIRED


def test_context_is_strict_with_a_bundle(tmp_path):
    ctx = system_trust.build_context({"AGENTBUNDLE_CA_BUNDLE": str(_real_pem(tmp_path))})
    assert ctx.check_hostname is True
    assert ctx.verify_mode is ssl.CERT_REQUIRED


def test_bundle_is_added_to_the_default_store_not_substituted(tmp_path):
    """The augment-not-replace property.

    A bundle holding one private CA must leave the public roots in place, or the
    github.com -> codeload.github.com redirect hop stops verifying.
    """
    default_ders = ssl.create_default_context().get_ca_certs(binary_form=True)
    if len(default_ders) < 2:
        pytest.skip("default store too small to distinguish augment from replace")

    # The bundle holds default_ders[0]. A *replace* implementation would leave
    # only that certificate trusted, so the presence of an unrelated public root
    # is what actually discriminates the two behaviours — a count comparison
    # cannot, because the bundled certificate is already in the default store.
    bystander = default_ders[1]
    ctx = system_trust.build_context({"AGENTBUNDLE_CA_BUNDLE": str(_real_pem(tmp_path))})
    assert bystander in ctx.get_ca_certs(binary_form=True), (
        "an unrelated public root was dropped — the bundle replaced the store"
    )


def test_system_anchors_flag_only_widens(monkeypatch, tmp_path):
    pem = _real_pem(tmp_path).read_text()
    monkeypatch.setattr(sys, "platform", "darwin")
    without = len(system_trust.build_context({}).get_ca_certs())
    with_anchors = system_trust.build_context({}, system_anchors=pem)
    assert len(with_anchors.get_ca_certs()) >= without
    assert with_anchors.check_hostname is True
    assert with_anchors.verify_mode is ssl.CERT_REQUIRED


# ---------------------------------------------------------------------------
# T2 — keychain export
# ---------------------------------------------------------------------------


def test_argv_covers_admin_keychains_and_never_the_login_keychain(monkeypatch, tmp_path):
    """The load-bearing security assertion of this feature.

    The login keychain is writable without administrator rights, so a root
    landing there is not an IT trust decision and must never be an anchor.
    """
    seen: list[list[str]] = []

    def runner(argv):
        seen.append(argv)
        return _real_pem(tmp_path).read_text()

    monkeypatch.setattr(system_trust, "_RUNNER", runner)
    monkeypatch.setattr(sys, "platform", "darwin")
    system_trust.system_anchor_pem()

    assert seen, "expected the keychain runner to be invoked"
    flat = " ".join(part for argv in seen for part in argv)
    assert "/Library/Keychains/System.keychain" in flat
    assert "SystemRootCertificates" not in flat, (
        "Apple's root program is deliberately not imported"
    )
    assert "login" not in flat.lower()


def test_non_darwin_returns_no_anchors_without_invoking_the_runner(monkeypatch):
    called = False

    def runner(argv):
        nonlocal called
        called = True
        return ""

    monkeypatch.setattr(system_trust, "_RUNNER", runner)
    monkeypatch.setattr(sys, "platform", "linux")
    assert system_trust.system_anchor_pem() is None
    assert called is False


def test_runner_failure_returns_no_anchors(monkeypatch):
    def runner(argv):
        raise OSError("security not found")

    monkeypatch.setattr(system_trust, "_RUNNER", runner)
    monkeypatch.setattr(sys, "platform", "darwin")
    assert system_trust.system_anchor_pem() is None


def test_runner_returning_no_pem_block_returns_no_anchors(monkeypatch):
    monkeypatch.setattr(system_trust, "_RUNNER", lambda argv: "not a certificate\n")
    monkeypatch.setattr(sys, "platform", "darwin")
    assert system_trust.system_anchor_pem() is None


def test_unreadable_anchor_material_does_not_break_context():
    """Garbage that survives the marker check must not abort the fetch.

    The default store must also survive it — anchors that fail to parse may not
    take the public roots down with them.
    """
    baseline = len(ssl.create_default_context().get_ca_certs())
    garbage = "-----BEGIN CERTIFICATE-----\nnot base64\n-----END CERTIFICATE-----\n"
    ctx = system_trust.build_context({}, system_anchors=garbage)
    assert ctx.verify_mode is ssl.CERT_REQUIRED
    assert len(ctx.get_ca_certs()) == baseline, "unparseable anchors cost the defaults"


def test_good_anchor_survives_a_malformed_block_in_the_dump(monkeypatch, tmp_path):
    """A keychain dump contains material OpenSSL cannot parse.

    ``cafile=`` loses every anchor when any block is malformed; ``cadata=``
    keeps the ones that parsed. A fallback that silently loads nothing while
    announcing itself is the worst outcome available, so this pins the
    forgiving form.
    """
    good = _real_pem(tmp_path).read_text()
    garbage = "-----BEGIN CERTIFICATE-----\nnot base64\n-----END CERTIFICATE-----\n"
    baseline = len(ssl.create_default_context().get_ca_certs())
    monkeypatch.setattr(sys, "platform", "darwin")
    ctx = system_trust.build_context({}, system_anchors=good + garbage)
    assert len(ctx.get_ca_certs()) >= baseline, "the parseable anchor was discarded"
    assert ctx.verify_mode is ssl.CERT_REQUIRED


def test_no_shipped_module_can_disable_verification():
    """Invariant across every shipped package, per CONVENTIONS.md:1201 and :1218.

    An --insecure escape hatch must not appear even as a debug convenience.

    Three ways an earlier version of this test failed open, all closed here:
    the root is anchored at the repository rather than derived from an installed
    module path (which resolved above site-packages and scanned nothing); only
    wheel-build copies under `build/lib/` are skipped, not the shipped bundler
    under `agentbundle/build/`; and a floor on the file count means the
    assertion cannot pass vacuously because it scanned zero files.

    `check_hostname = False` is in the token list because it re-enables
    machine-in-the-middle interception while leaving `CERT_REQUIRED` in place, so
    every other assertion in this file would stay green with verification off.
    """
    packages_root = Path(__file__).resolve().parents[3]
    assert packages_root.name == "packages", f"unexpected root: {packages_root}"

    forbidden = (
        "CERT_NONE",
        "CERT_OPTIONAL",
        "verify=False",
        "_create_unverified_context",
        "check_hostname = False",
        "check_hostname=False",
        '"--insecure"',  # argparse spelling; bare text matches prose forbidding it
    )
    scanned = 0
    offenders = []
    for path in sorted(packages_root.glob("*/**/*.py")):
        rel = path.relative_to(packages_root)
        parts = rel.parts
        if "tests" in parts or path.name.startswith("test_"):
            continue
        if "build" in parts and "lib" in parts:
            continue  # wheel-build copy, not shipped source
        scanned += 1
        text = path.read_text(encoding="utf-8")
        offenders.extend(f"{rel}: {tok}" for tok in forbidden if tok in text)

    assert scanned > 50, f"scanned only {scanned} files — the glob is wrong"
    assert offenders == [], f"verification-disabling constructs found: {offenders}"


def test_the_default_keychain_tuple_is_administrator_only():
    """The *default* mode consults the administrator store and nothing else.

    Scoped deliberately: the empty-store mode does reach Apple's public TLS
    export (RFC-0086 Errata). With any working trust store this holds, because
    the retry already carries Python's own roots and a second root program would
    widen trust for no gain on a fetch path with no post-transport integrity
    check.
    """
    joined = " ".join(system_trust._ADMIN_KEYCHAINS)
    assert "/Library/Keychains/System.keychain" in joined
    assert "SystemRootCertificates" not in joined
    assert "login" not in joined.lower()


def test_a_malformed_block_first_does_not_discard_later_anchors():
    """OpenSSL stops at the first unparseable block, so order must not matter.

    A combined load keeps 0 anchors when the garbage comes first. Per-block
    loading is what makes the corporate root survive a dirty dump.
    """
    ders = ssl.create_default_context().get_ca_certs(binary_form=True)
    if not ders:
        pytest.skip("interpreter has an empty default trust store")
    good = ssl.DER_cert_to_PEM_cert(ders[0])
    garbage = "-----BEGIN CERTIFICATE-----\nnot base64\n-----END CERTIFICATE-----\n"

    fresh = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    system_trust._load_pem_text(fresh, garbage + good)
    assert len(fresh.get_ca_certs()) == 1, "a leading bad block discarded the good one"

    reverse = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    system_trust._load_pem_text(reverse, good + garbage)
    assert len(reverse.get_ca_certs()) == 1, "a trailing bad block discarded the good one"


def test_non_ascii_anchor_material_does_not_crash(monkeypatch):
    """`cadata` rejects non-ASCII str with TypeError, which is not a ValueError."""
    ctx = system_trust.build_context({}, system_anchors="-----BEGIN CERTIFICATE-----\n\u00e9\n-----END CERTIFICATE-----\n")
    assert ctx.verify_mode is ssl.CERT_REQUIRED


def test_a_undecodable_dump_does_not_escape(monkeypatch):
    """The runner decodes strictly; a UnicodeDecodeError must not escape."""
    def runner(argv):
        raise UnicodeDecodeError("utf-8", b"\xff", 0, 1, "invalid start byte")

    monkeypatch.setattr(system_trust, "_RUNNER", runner)
    monkeypatch.setattr(sys, "platform", "darwin")
    assert system_trust.system_anchor_pem() is None


def test_a_process_wide_ssl_override_cannot_weaken_the_context(monkeypatch):
    """Constructing the context explicitly is the point, per credbroker/_sso.py.

    A global ``ssl._create_default_https_context`` override must not reach the
    request that decides which code an adopter installs.
    """
    monkeypatch.setattr(
        ssl, "_create_default_https_context", ssl._create_unverified_context
    )
    ctx = system_trust.build_context({})
    assert ctx.verify_mode is ssl.CERT_REQUIRED, "a global override weakened the fetch"
    assert ctx.check_hostname is True


# ---------------------------------------------------------------------------
# Empty default trust store — RFC-0086 erratum
# ---------------------------------------------------------------------------


def test_empty_store_is_detected(monkeypatch, tmp_path):
    """The field case: a python.org interpreter with no certificates configured.

    Reproduced by pointing SSL_CERT_FILE at an empty PEM, which is what an
    unconfigured interpreter reports as: cafile set, zero anchors loaded.
    """
    empty = tmp_path / "empty.pem"
    empty.write_text("")
    # Must be the real environment, not an injected mapping: OpenSSL resolves
    # SSL_CERT_FILE through its own default paths inside create_default_context,
    # before this code sees it. An injected dict cannot reproduce the state.
    monkeypatch.setenv("SSL_CERT_FILE", str(empty))
    monkeypatch.setenv("SSL_CERT_DIR", str(tmp_path / "no-such-dir"))
    assert system_trust.default_store_is_empty() is True


def test_intact_store_is_not_reported_empty():
    if not ssl.create_default_context().get_ca_certs():
        pytest.skip("this interpreter genuinely has an empty store")
    assert system_trust.default_store_is_empty({}) is False


def test_apple_roots_are_read_only_when_the_store_is_empty(monkeypatch, tmp_path):
    """The erratum's whole point, and the bound on it.

    RFC-0086 D4 excluded Apple's root program outright. That was too broad: an
    interpreter trusting nothing cannot be repaired from the administrator
    keychain, which holds private roots. It stays excluded with an intact store.
    """
    seen: list[list[str]] = []

    def runner(argv):
        seen.append(argv)
        return _real_pem(tmp_path).read_text()

    monkeypatch.setattr(system_trust, "_RUNNER", runner)
    monkeypatch.setattr(sys, "platform", "darwin")

    admin_only = system_trust.system_anchor_pem()
    flat = " ".join(part for argv in seen for part in argv)
    assert "/Library/Keychains/System.keychain" in flat
    assert "SystemRootCertificates" not in flat, "intact store must not read Apple's roots"
    assert "login" not in flat.lower()

    seen.clear()
    widened = system_trust.system_anchor_pem(include_public_roots=True)
    flat = " ".join(part for argv in seen for part in argv)
    assert "/Library/Keychains/System.keychain" in flat, "admin keychain still read"
    assert "login" not in flat.lower(), "login keychain never read, in either mode"
    # Public roots come from Apple's TLS-purpose export, not a keychain dump: the
    # dump carries code-signing and Apple-operated roots that /etc/ssl/cert.pem
    # excludes, and reading the file needs no subprocess at all.
    if Path(system_trust._APPLE_TLS_BUNDLE).is_file():
        assert "SystemRootCertificates" not in flat, (
            "the keychain is a fallback only, used when the export is missing"
        )
        assert widened is not None
        assert widened.count("BEGIN CERTIFICATE") > admin_only.count("BEGIN CERTIFICATE")


def test_empty_store_detection_survives_a_broken_bundle(monkeypatch, tmp_path):
    """A stale path must not make the helper raise inside an except block."""
    # AGENTBUNDLE_CA_BUNDLE is the one that raises CatalogueError on a missing
    # path; REQUESTS_CA_BUNDLE never does, so testing it proved nothing.
    monkeypatch.setenv("AGENTBUNDLE_CA_BUNDLE", str(tmp_path / "absent.pem"))
    assert system_trust.default_store_is_empty() is False
