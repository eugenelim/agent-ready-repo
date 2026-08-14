"""Two-attempt catalogue fetch — spec/catalogue-corporate-trust-store T3/T4.

Coverage:
  T3 — retry sequencing, opt-out, unchanged single-connection path
  T4 — remediation text, explicit timeout

``urlopen`` is stubbed throughout; no real network calls. Placeholder host names
only, per the convention in test_https_catalogue.py.
"""

from __future__ import annotations

import io
import os
import ssl
import sys
import tarfile
import types
import urllib.error
import urllib.request

import pytest
from agentbundle import catalogue, system_trust
from agentbundle.catalogue import CatalogueError

URL = "https://example.test/owner/repo/archive/refs/heads/main.tar.gz"


def _tarball() -> bytes:
    """A minimal, valid gzip tarball with one top-level directory."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        payload = b"catalogue\n"
        info = tarfile.TarInfo("repo-main/pack.toml")
        info.size = len(payload)
        tf.addfile(info, io.BytesIO(payload))
    return buf.getvalue()


def _verify_error() -> urllib.error.URLError:
    """The real shape urllib produces: URLError wrapping the SSL error.

    urlopen never lets ssl.SSLCertVerificationError escape directly, so a fetch
    that matched on the bare exception type would never fire the fallback.
    """
    return urllib.error.URLError(
        ssl.SSLCertVerificationError(
            1,
            "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: "
            "unable to get local issuer certificate (_ssl.c:1032)",
        )
    )


class _Stub:
    """Records each urlopen call and replays a scripted outcome per call."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls: list[dict] = []

    def __call__(self, url, *args, **kwargs):
        self.calls.append({"url": url, "kwargs": kwargs})
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return io.BytesIO(outcome)


@pytest.fixture
def no_env(monkeypatch):
    for var in (
        "AGENTBUNDLE_CA_BUNDLE",
        "AGENTBUNDLE_NO_SYSTEM_TRUST",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
    ):
        monkeypatch.delenv(var, raising=False)


# ---------------------------------------------------------------------------
# T3 — sequencing
# ---------------------------------------------------------------------------


def test_clean_verification_makes_exactly_one_connection(monkeypatch, tmp_path, no_env):
    """The unchanged-behaviour guarantee."""
    stub = _Stub([_tarball()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    catalogue._fetch_and_extract(URL, tmp_path)
    assert len(stub.calls) == 1
    assert (tmp_path / "repo-main" / "pack.toml").exists()


def _an_anchor_pem() -> str:
    """A real, parseable CA certificate to stand in for keychain material."""
    ders = ssl.create_default_context().get_ca_certs(binary_form=True)
    if not ders:
        pytest.skip("interpreter has an empty default trust store")
    return ssl.DER_cert_to_PEM_cert(ders[0])


def test_verification_failure_retries_once_with_system_anchors(
    monkeypatch, tmp_path, capsys, no_env
):
    stub = _Stub([_verify_error(), _tarball()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: _an_anchor_pem())

    catalogue._fetch_and_extract(URL, tmp_path)

    assert len(stub.calls) == 2, "expected exactly one retry"
    assert (tmp_path / "repo-main" / "pack.toml").exists()
    captured = capsys.readouterr()
    assert "example.test" in captured.err
    assert captured.out == "", "nothing may go to stdout"


def test_retry_uses_a_different_context_carrying_the_anchors(
    monkeypatch, tmp_path, no_env
):
    """Without this, the retry could re-dial the same context and still pass.

    The previous version of this test stubbed the anchors to None, so it would
    have passed against an implementation that dropped the anchors entirely.
    """
    stub = _Stub([_verify_error(), _tarball()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: _an_anchor_pem())

    catalogue._fetch_and_extract(URL, tmp_path)

    first = stub.calls[0]["kwargs"]["context"]
    second = stub.calls[1]["kwargs"]["context"]
    assert second is not first, "the retry must build a fresh context"
    assert second.verify_mode is ssl.CERT_REQUIRED
    assert second.check_hostname is True


def test_no_retry_when_no_system_anchors_are_available(
    monkeypatch, tmp_path, capsys, no_env
):
    """On a platform with no administrator trust store, do not pretend.

    A second connection against an identical context is noise, and announcing
    anchors that were never consulted misdirects the adopter.
    """
    monkeypatch.setattr(sys, "platform", "linux")
    stub = _Stub([_verify_error()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: None)

    with pytest.raises(CatalogueError) as exc:
        catalogue._fetch_and_extract(URL, tmp_path)

    assert len(stub.calls) == 1, "must not re-dial with an identical context"
    assert "macOS-only" in str(exc.value)
    assert "retrying with" not in capsys.readouterr().err


def test_empty_admin_keychain_on_macos_names_the_real_cause(
    monkeypatch, tmp_path, capsys, no_env
):
    """On macOS the fallback DID apply — it just found nothing.

    Blaming the platform here would misdirect an adopter whose authority is
    installed in a store this deliberately does not read.
    """
    monkeypatch.setattr(sys, "platform", "darwin")
    stub = _Stub([_verify_error()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: None)

    with pytest.raises(CatalogueError) as exc:
        catalogue._fetch_and_extract(URL, tmp_path)

    message = str(exc.value)
    assert "administrator keychain holds no certificates" in message
    assert "macOS-only" not in message, "must not blame the platform on macOS"
    assert len(stub.calls) == 1


def test_fallback_notice_fires_once(monkeypatch, tmp_path, capsys, no_env):
    stub = _Stub([_verify_error(), _tarball()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: _an_anchor_pem())
    catalogue._fetch_and_extract(URL, tmp_path)
    err = capsys.readouterr().err
    assert err.count("retrying with operating-system trust anchors") == 1, err


def test_non_certificate_error_does_not_retry(monkeypatch, tmp_path, no_env):
    """A timeout must not become doubled load."""
    stub = _Stub([urllib.error.URLError(TimeoutError("timed out"))])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    with pytest.raises(CatalogueError):
        catalogue._fetch_and_extract(URL, tmp_path)
    assert len(stub.calls) == 1


def test_opt_out_suppresses_the_retry(monkeypatch, tmp_path, no_env):
    monkeypatch.setenv("AGENTBUNDLE_NO_SYSTEM_TRUST", "1")
    stub = _Stub([_verify_error()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    with pytest.raises(CatalogueError) as exc:
        catalogue._fetch_and_extract(URL, tmp_path)
    assert len(stub.calls) == 1, "opt-out must not retry"
    message = str(exc.value)
    assert "CERTIFICATE_VERIFY_FAILED" in message
    assert "was not attempted" in message, "must say the fallback did not run"
    assert "did not complete the chain" not in message, (
        "must not claim anchors were exhausted when they were never consulted"
    )
    assert "Set AGENTBUNDLE_NO_SYSTEM_TRUST=1" not in message, (
        "must not advise setting a variable the adopter has already set"
    )


def test_retry_failure_raises_catalogue_error(monkeypatch, tmp_path, no_env):
    stub = _Stub([_verify_error(), _verify_error()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: _an_anchor_pem())
    with pytest.raises(CatalogueError):
        catalogue._fetch_and_extract(URL, tmp_path)
    assert len(stub.calls) == 2


# ---------------------------------------------------------------------------
# T4 — remediation text and timeout
# ---------------------------------------------------------------------------


def test_unrepairable_failure_names_cause_and_next_action(monkeypatch, tmp_path, no_env):
    stub = _Stub([_verify_error(), _verify_error()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: _an_anchor_pem())
    with pytest.raises(CatalogueError) as exc:
        catalogue._fetch_and_extract(URL, tmp_path)
    message = str(exc.value)
    assert "inspect" in message.lower(), "must name the probable cause"
    assert "AGENTBUNDLE_CA_BUNDLE" in message, "must name the next action"
    assert URL in message, "must keep naming what was attempted"
    assert "local clone" in message, "must offer the no-HTTPS route"
    assert "codeload.github.com" in message, "must name the second-host wall"


def test_message_does_not_recommend_a_virtualenv_as_a_fix(monkeypatch, tmp_path, no_env):
    """A venv inherits its base interpreter's trust store unchanged.

    Recommending one is cargo-cult: it appears to work only when the venv was
    built from a *different* interpreter whose store already trusted the
    network. The message must point at the interpreter, not the venv.
    """
    stub = _Stub([_verify_error(), _verify_error()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: _an_anchor_pem())
    with pytest.raises(CatalogueError) as exc:
        catalogue._fetch_and_extract(URL, tmp_path)
    message = str(exc.value)
    assert "get_default_verify_paths" in message, "must show how to compare stores"
    assert "does NOT change trust" in message, "must debunk the venv folk remedy"


def test_fetch_passes_an_explicit_timeout(monkeypatch, tmp_path, no_env):
    stub = _Stub([_tarball()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    catalogue._fetch_and_extract(URL, tmp_path)
    assert stub.calls[0]["kwargs"].get("timeout"), "a black-holing proxy must not hang"


def test_missing_ca_bundle_path_still_raises_before_any_connection(
    monkeypatch, tmp_path, no_env
):
    monkeypatch.setenv("AGENTBUNDLE_CA_BUNDLE", str(tmp_path / "absent.pem"))
    stub = _Stub([_tarball()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)
    with pytest.raises(CatalogueError) as exc:
        catalogue._fetch_and_extract(URL, tmp_path)
    assert "absent.pem" in str(exc.value)
    assert not stub.calls, "a typo must be caught before dialing out"


def test_read_phase_failures_are_wrapped_not_leaked(monkeypatch, tmp_path, no_env):
    """A stall or TLS error mid-body escapes urlopen unwrapped.

    urlopen only wraps connect-phase failures, so these reach the caller as
    bare exceptions and would break the module's documented promise that an
    unreachable URL raises CatalogueError.
    """
    for raw in (TimeoutError("read timed out"), ssl.SSLError("decryption failed")):
        stub = _Stub([raw])
        monkeypatch.setattr(urllib.request, "urlopen", stub)
        with pytest.raises(CatalogueError) as exc:
            catalogue._fetch_and_extract(URL, tmp_path)
        assert URL in str(exc.value)
        assert len(stub.calls) == 1, "a non-certificate failure must not retry"


def test_empty_store_message_names_the_real_cause(monkeypatch, tmp_path, no_env):
    """Your user's exact state: zero anchors, no proxy, admin keychain no help.

    The old message blamed a TLS-inspecting proxy, which was actively
    misleading — nothing was intercepting them.
    """
    monkeypatch.setattr(sys, "platform", "darwin")
    monkeypatch.setattr(system_trust, "default_store_is_empty", lambda *a, **k: True)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: _an_anchor_pem())
    stub = _Stub([_verify_error(), _verify_error()])
    monkeypatch.setattr(urllib.request, "urlopen", stub)

    with pytest.raises(CatalogueError) as exc:
        catalogue._fetch_and_extract(URL, tmp_path)

    message = str(exc.value)
    assert "trusts ZERO certificate authorities" in message
    assert "3.x" not in message, "the version placeholder must never reach an adopter"
    # Softened from an absolute after security review: a populated capath is
    # excluded before we get here, but a store can still be empty AND the
    # network inspected.
    assert "almost certainly not a corporate-proxy" in message
    assert "TLS-inspecting proxy" not in message, "must not blame a proxy here"


def test_empty_store_asks_for_public_roots(monkeypatch, tmp_path, no_env):
    """The fallback must widen to Apple's roots only in the empty-store case."""
    calls: list[bool] = []

    def anchors(*, include_public_roots: bool = False):
        calls.append(include_public_roots)
        return _an_anchor_pem()

    monkeypatch.setattr(system_trust, "system_anchor_pem", anchors)
    monkeypatch.setattr(urllib.request, "urlopen", _Stub([_verify_error(), _tarball()]))

    monkeypatch.setattr(system_trust, "default_store_is_empty", lambda *a, **k: True)
    catalogue._fetch_and_extract(URL, tmp_path)
    assert calls == [True], "empty store must request the public roots"

    calls.clear()
    monkeypatch.setattr(system_trust, "default_store_is_empty", lambda *a, **k: False)
    monkeypatch.setattr(urllib.request, "urlopen", _Stub([_verify_error(), _tarball()]))
    catalogue._fetch_and_extract(URL, tmp_path)
    assert calls == [False], "intact store must not request the public roots"


def test_successful_empty_store_recovery_still_tells_the_adopter(
    monkeypatch, tmp_path, capsys, no_env
):
    """Recovering the fetch must not silently mask a broken interpreter.

    The anchors are loaded in memory for this process only, so the adopter's
    next pip or requests call fails the same way. A green install with no
    explanation is how that goes unnoticed.
    """
    monkeypatch.setattr(system_trust, "default_store_is_empty", lambda *a, **k: True)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: _an_anchor_pem())
    monkeypatch.setattr(urllib.request, "urlopen", _Stub([_verify_error(), _tarball()]))

    monkeypatch.setattr(sys, "platform", "darwin")
    # Pin the hint too, not just the platform: the command is derived from the
    # running interpreter's version and only exists on a python.org framework
    # build, so asserting it unpinned depends on the developer's machine.
    monkeypatch.setattr(
        catalogue,
        "_install_certificates_hint",
        lambda: 'open "/Applications/Python 3.14/Install Certificates.command"',
    )
    catalogue._fetch_and_extract(URL, tmp_path)

    err = capsys.readouterr().err
    assert "trusts no certificate authorities" in err
    assert "does not fix the interpreter" in err
    assert "Install Certificates.command" in err
    assert "3.x" not in err, "the version placeholder must never reach an adopter"
    assert (tmp_path / "repo-main" / "pack.toml").exists(), "install must still succeed"


def test_empty_store_notice_off_macos_omits_mac_only_advice(
    monkeypatch, tmp_path, capsys, no_env
):
    """The same misdirection this change removes, in the other direction.

    Telling a Linux adopter to open an /Applications path is the macOS-only
    remedy leaking onto a platform that cannot use it.
    """
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setattr(system_trust, "default_store_is_empty", lambda *a, **k: True)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: _an_anchor_pem())
    monkeypatch.setattr(urllib.request, "urlopen", _Stub([_verify_error(), _tarball()]))

    catalogue._fetch_and_extract(URL, tmp_path)

    err = capsys.readouterr().err
    assert "trusts no certificate authorities" in err
    assert "Install Certificates.command" not in err
    assert "SSL_CERT_FILE" in err


def test_intact_store_recovery_keeps_the_short_notice(
    monkeypatch, tmp_path, capsys, no_env
):
    """The corporate case is not an unconfigured interpreter — don't say it is."""
    monkeypatch.setattr(system_trust, "default_store_is_empty", lambda *a, **k: False)
    monkeypatch.setattr(system_trust, "system_anchor_pem", lambda **k: _an_anchor_pem())
    monkeypatch.setattr(urllib.request, "urlopen", _Stub([_verify_error(), _tarball()]))

    catalogue._fetch_and_extract(URL, tmp_path)

    err = capsys.readouterr().err
    assert "retrying with operating-system trust anchors" in err
    assert "trusts no certificate authorities" not in err


def _tarball_with_symlink() -> bytes:
    """A catalogue-shaped archive: a regular file, then a symlink pointing back.

    This is the real shape — the catalogue carries CLAUDE.md -> AGENTS.md, and
    the target precedes the link in the archive.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        payload = b"# agents\n"
        target = tarfile.TarInfo("repo-main/AGENTS.md")
        target.size = len(payload)
        tf.addfile(target, io.BytesIO(payload))
        link = tarfile.TarInfo("repo-main/CLAUDE.md")
        link.type = tarfile.SYMTYPE
        link.linkname = "AGENTS.md"
        tf.addfile(link)
    return buf.getvalue()


def test_symlink_archive_extracts_where_symlinks_cannot_be_created(
    monkeypatch, tmp_path, no_env
):
    """Windows regression: os.symlink fails, so tarfile copies the target instead.

    That fallback re-reads a member that already went past, which a forward-only
    stream cannot do — the field error was
    'seeking backwards is not allowed'. Simulated here by making os.symlink
    fail, so the case is covered on every platform rather than only on Windows.
    """
    def no_symlinks(*a, **k):
        raise OSError("symbolic link privilege not held")

    monkeypatch.setattr(os, "symlink", no_symlinks)
    monkeypatch.setattr(
        urllib.request, "urlopen", _Stub([_tarball_with_symlink()])
    )

    catalogue._fetch_and_extract(URL, tmp_path)

    assert (tmp_path / "repo-main" / "AGENTS.md").exists()
    claude = tmp_path / "repo-main" / "CLAUDE.md"
    assert claude.exists(), "the link target must be copied when links are unavailable"
    assert claude.read_text() == "# agents\n", "copy must carry the target's content"


def test_certificate_hint_carries_a_real_version_or_is_omitted(monkeypatch, tmp_path):
    """Never print a path an adopter has to edit before it works.

    The hint is derived from the running interpreter and returned only when the
    script actually exists, so a non-framework build gets the portable advice
    instead of a command that would fail.
    """
    hint = catalogue._install_certificates_hint()
    if hint is not None:
        assert "3.x" not in hint
        assert f"{sys.version_info.major}.{sys.version_info.minor}" in hint

    # A version whose script cannot exist must yield no hint at all. A bare
    # tuple will not do: the code reads .major/.minor off version_info.
    monkeypatch.setattr(
        catalogue.sys,
        "version_info",
        types.SimpleNamespace(major=3, minor=99),
        raising=False,
    )
    assert catalogue._install_certificates_hint() is None
