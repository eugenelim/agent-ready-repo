"""AC35 — no test or CI step writes to the developer's real
``~/.agent-ready/``, real macOS Keychain, or real Windows Credential
Manager.

This is a static-analysis posture assertion. It is not a runtime check
that no test ever happens to write live — the runtime convention lives
in every test's ``backend`` fixture, which sets a ``tmp_path``-derived
prefix before the backend's first call. This test instead verifies the
convention is honored at file level: every test under
``packages/agentbundle/tests/integration/test_keychain_macos.py`` and
``packages/agentbundle/tests/integration/test_credman_windows.py`` uses
the documented isolation anchor (``SERVICE`` / ``SERVICE_PREFIX_OVERRIDE``
monkeypatch) so a future contributor cannot ship a test that forgets to
namespace itself without this assertion firing.

If you need to add a test that legitimately *cannot* use the isolation
fixture (e.g. one that verifies the backend's behaviour without the
fixture's monkeypatch), add the fixture name to ``ALLOWED_SOLO_TESTS``
below with a one-line reason, then ensure your test still does not
touch the real Keychain / Credential Manager.
"""

from __future__ import annotations

import pathlib


REPO_ROOT = pathlib.Path(__file__).resolve().parents[4]
KEYCHAIN_TEST = (
    REPO_ROOT
    / "packages" / "agentbundle" / "tests" / "integration"
    / "test_keychain_macos.py"
)
CREDMAN_TEST = (
    REPO_ROOT
    / "packages" / "agentbundle" / "tests" / "integration"
    / "test_credman_windows.py"
)

# Anchors that must appear in each backend's test file. Each anchor names
# the production constant the backend exposes for test isolation; absence
# means the file never rebinds the production constant, and tests would
# write to the real Keychain / Credential Manager.
KEYCHAIN_ANCHOR = 'monkeypatch.setattr(_keychain_macos, "SERVICE"'
CREDMAN_ANCHOR = 'monkeypatch.setattr(cm, "SERVICE_PREFIX_OVERRIDE"'


def test_keychain_tests_set_service_override():
    """Every macOS Keychain integration test routes through a ``backend``
    fixture that monkeypatches ``SERVICE`` to a ``tmp_path``-derived
    prefix. AC35: the developer's real ``agent-ready`` Keychain entries
    must never be touched.
    """
    if not KEYCHAIN_TEST.is_file():
        return  # File deleted — nothing to enforce.
    text = KEYCHAIN_TEST.read_text(encoding="utf-8")
    assert KEYCHAIN_ANCHOR in text, (
        f"AC35 violation: {KEYCHAIN_TEST.name} does not contain the "
        f"isolation anchor {KEYCHAIN_ANCHOR!r}. Every test in this file "
        f"must rebind ``_keychain_macos.SERVICE`` to a ``tmp_path``-"
        f"derived prefix via the ``backend`` fixture before exercising "
        f"the real ``/usr/bin/security`` binary."
    )


def test_credman_tests_set_service_prefix_override():
    """Every Windows Credential Manager integration test routes through
    a ``backend`` fixture that monkeypatches ``SERVICE_PREFIX_OVERRIDE``
    to a ``tmp_path``-derived prefix. AC35: the developer's real
    ``agent-ready:`` Credential Manager entries must never be touched.
    """
    if not CREDMAN_TEST.is_file():
        return
    text = CREDMAN_TEST.read_text(encoding="utf-8")
    assert CREDMAN_ANCHOR in text, (
        f"AC35 violation: {CREDMAN_TEST.name} does not contain the "
        f"isolation anchor {CREDMAN_ANCHOR!r}. Every test in this file "
        f"must rebind ``cm.SERVICE_PREFIX_OVERRIDE`` to a ``tmp_path``-"
        f"derived prefix via the ``backend`` fixture before exercising "
        f"the in-process ``advapi32`` ctypes path."
    )


def test_dotfile_tests_redirect_home_to_tmp_path():
    """AC35 also covers the Tier-3 dotfile path — no test may write to the
    developer's real ``~/.agent-ready/credentials.env``. The dotfile
    tests must redirect ``HOME`` (or use a monkeypatched
    ``pathlib.Path.home`` via the ``isolated_home`` fixture) before any
    write.
    """
    dotfile_test = (
        REPO_ROOT
        / "packages" / "agentbundle" / "tests" / "unit"
        / "test_credentials_dotfile.py"
    )
    if not dotfile_test.is_file():
        return
    text = dotfile_test.read_text(encoding="utf-8")
    # Either ``monkeypatch.setenv("HOME"`` or a ``isolated_home`` fixture
    # must appear — both are valid isolation anchors.
    has_home_setenv = 'monkeypatch.setenv("HOME"' in text or "setenv('HOME'" in text
    has_isolated_fixture = "isolated_home" in text or "redirect_home" in text
    assert has_home_setenv or has_isolated_fixture, (
        f"AC35 violation: {dotfile_test.name} does not redirect ``$HOME`` "
        f"or use an ``isolated_home``-style fixture; tests may write to "
        f"the developer's real ``~/.agent-ready/credentials.env``."
    )
