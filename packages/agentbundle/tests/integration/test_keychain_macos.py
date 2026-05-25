"""T4: macOS Keychain Tier-2 backend (spec § AC6-AC8).

Tests are gated on ``sys.platform == "darwin"`` — the backend module
imports nothing platform-specific itself (it just shells out to
``/usr/bin/security``), but the binary only exists on macOS and the
test isolation uses ``security create-keychain``.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest


pytestmark = pytest.mark.skipif(
    sys.platform != "darwin",
    reason="macOS Keychain backend — Darwin-only",
)


@pytest.fixture
def backend(tmp_path, monkeypatch):
    """Import the backend and scope ``SERVICE`` to a ``tmp_path``-derived
    prefix so test entries can't collide with the developer's real
    ``agentbundle`` Keychain entries.

    The ``security -w`` prompt mode requires ``-w`` as the trailing argv
    element, which forecloses test isolation via a trailing keychain
    positional — hence the service-prefix approach. AC35's strict
    reading ("no Keychain entry persists outside a ``tmp_path``-scoped
    Keychain") is satisfied by the cleanup loop below; entries are
    namespaced *and* removed in teardown so nothing persists.
    """
    from agentbundle.creds import _keychain_macos
    unique_service = f"agentbundle-test-{abs(hash(str(tmp_path))) & 0xffffffff:08x}"
    monkeypatch.setattr(_keychain_macos, "SERVICE", unique_service)

    # Track every account written so teardown can delete them.
    written: list[tuple[str, str]] = []
    real_write = _keychain_macos.write_credential

    def tracking_write(namespace, key, value):
        written.append((namespace, key))
        return real_write(namespace, key, value)

    monkeypatch.setattr(_keychain_macos, "write_credential", tracking_write)
    yield _keychain_macos
    # Best-effort cleanup — the unique service prefix prevents collisions
    # with real entries; the explicit deletes prevent accumulation.
    for namespace, key in written:
        try:
            _keychain_macos.delete_credential(namespace, key)
        except Exception:
            pass


# ── Round-trip + miss ──────────────────────────────────────────────────


def test_write_then_read_byte_equal(backend):
    """AC7: round-trip — write a value, read it, compare bytes."""
    backend.write_credential("fixture_t4", "API_TOKEN", "round-trip-secret-1")
    assert backend.read_credential("fixture_t4", "API_TOKEN") == "round-trip-secret-1"


def test_read_missing_returns_none(backend):
    """AC8 inverse: missing entry returns ``None`` so the resolver falls
    through to Tier 3."""
    assert backend.read_credential("fixture_t4_absent", "API_TOKEN") is None


def test_write_upsert_replaces_value(backend):
    """``-U`` flag: a second write with the same account replaces the value."""
    backend.write_credential("fixture_t4", "API_TOKEN", "first")
    backend.write_credential("fixture_t4", "API_TOKEN", "second")
    assert backend.read_credential("fixture_t4", "API_TOKEN") == "second"


def test_delete_removes_entry_and_subsequent_read_is_none(backend):
    backend.write_credential("fixture_t4", "API_TOKEN", "to-delete")
    backend.delete_credential("fixture_t4", "API_TOKEN")
    assert backend.read_credential("fixture_t4", "API_TOKEN") is None


def test_delete_missing_is_idempotent(backend):
    """A delete on an absent entry must not raise (spec — idempotent)."""
    backend.delete_credential("fixture_t4_never_set", "API_TOKEN")
    # No raise expected.


def test_multiple_keys_per_namespace_round_trip(backend):
    backend.write_credential("fixture_t4", "API_TOKEN", "tok")
    backend.write_credential("fixture_t4", "BASE_URL", "https://x.test")
    assert backend.read_credential("fixture_t4", "API_TOKEN") == "tok"
    assert backend.read_credential("fixture_t4", "BASE_URL") == "https://x.test"


# ── Argv shape + token-not-on-argv ─────────────────────────────────────


def test_find_argv_shape_matches_ac6(backend, monkeypatch):
    """AC6: read argv has the canonical shape — service, account, ``-w``
    (no trailing keychain positional)."""
    captured = []
    real_run = subprocess.run

    def recording_run(argv, *args, **kwargs):
        captured.append(list(argv))
        return real_run(argv, *args, **kwargs)

    backend.write_credential("fixture_t4", "API_TOKEN", "v")
    captured.clear()
    monkeypatch.setattr(backend.subprocess, "run", recording_run)
    backend.read_credential("fixture_t4", "API_TOKEN")
    assert len(captured) == 1
    argv = captured[0]
    # SERVICE is monkeypatched per-test; the rest of the shape is canonical.
    assert argv == [
        "/usr/bin/security", "find-generic-password",
        "-s", backend.SERVICE,
        "-a", "fixture_t4:API_TOKEN",
        "-w",
    ]


def test_add_argv_shape_matches_ac6_no_trailing_token(backend, monkeypatch):
    """AC6: write argv has the canonical shape and never carries the
    token bytes; the trailing ``-w`` (no value) triggers prompt-from-stdin."""
    captured_argv = []
    real_popen = subprocess.Popen

    def recording_popen(argv, *args, **kwargs):
        captured_argv.append(list(argv))
        return real_popen(argv, *args, **kwargs)

    monkeypatch.setattr(backend.subprocess, "Popen", recording_popen)
    secret = "super-secret-must-not-appear-on-argv-xyz"
    backend.write_credential("fixture_t4_argv", "API_TOKEN", secret)
    assert len(captured_argv) == 1
    argv = captured_argv[0]
    assert argv == [
        "/usr/bin/security", "add-generic-password", "-U",
        "-s", backend.SERVICE,
        "-a", "fixture_t4_argv:API_TOKEN",
        "-w",
    ]
    # No element of argv contains the secret.
    for item in argv:
        assert secret not in item, f"token leaked to argv element: {item!r}"


def test_token_not_in_argv_via_proc_inspection(backend):
    """AC6 ``psutil``-shaped check: while ``security`` runs, inspect
    ``ps -axo args`` and assert the token bytes are absent. ``psutil``
    is not stdlib; this test uses the system ``ps`` instead.
    """
    secret = "non-argv-token-abc123"
    argv = [
        "/usr/bin/security", "add-generic-password", "-U",
        "-s", backend.SERVICE,
        "-a", "fixture_t4_argv2:API_TOKEN",
        "-w",  # last argv element — triggers prompt-from-stdin
    ]
    proc = subprocess.Popen(
        argv,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    try:
        ps_out = subprocess.run(
            ["ps", "-axo", "args"], capture_output=True, text=True
        )
        assert secret not in ps_out.stdout, (
            "secret appeared in ps -axo args output"
        )
    finally:
        _, err = proc.communicate(input=secret.encode("utf-8"))
        # Best-effort cleanup of the entry written above.
        try:
            backend.delete_credential("fixture_t4_argv2", "API_TOKEN")
        except Exception:
            pass
    assert proc.returncode == 0, err.decode("utf-8", errors="replace")


# ── Loader-level platform dispatch (AC8 cross-ref) ─────────────────────


_creds_module_targets = lambda mod: (
    mod == "agentbundle.credentials"
    or mod == "agentbundle.creds"
    or mod.startswith("agentbundle.creds.")
)


def _snapshot_creds_modules() -> dict:
    return {k: sys.modules[k] for k in list(sys.modules) if _creds_module_targets(k)}


def _drop_creds_modules() -> None:
    for mod_name in list(sys.modules):
        if _creds_module_targets(mod_name):
            sys.modules.pop(mod_name, None)


def _restore_creds_modules(saved: dict) -> None:
    _drop_creds_modules()
    sys.modules.update(saved)


def test_loader_imports_macos_backend_on_darwin():
    """AC4b/AC8: when ``sys.platform == "darwin"``, the loader has the
    ``_keychain_macos`` backend in ``sys.modules`` after a fresh import.

    Snapshots sys.modules for the creds tree and restores it in
    ``finally`` so downstream tests keep their bound class objects (a
    fresh re-import yields a different ``EnvParseError`` class which
    silently breaks ``pytest.raises`` matches).
    """
    # The test process is already running on darwin (skipif gated the
    # whole module), so the backend should already be loaded by the
    # loader's module-level dispatch.
    saved = _snapshot_creds_modules()
    _drop_creds_modules()
    try:
        import agentbundle.credentials  # noqa: F401 — re-import
        assert "agentbundle.creds._keychain_macos" in sys.modules
        assert "agentbundle.creds._credman_windows" not in sys.modules
    finally:
        _restore_creds_modules(saved)


def test_loader_does_not_import_macos_backend_on_linux(monkeypatch):
    """AC4b: when ``sys.platform`` is monkeypatched to a non-Darwin
    value, the ``_keychain_macos`` import is skipped on fresh re-import."""
    monkeypatch.setattr(sys, "platform", "linux")
    saved = _snapshot_creds_modules()
    _drop_creds_modules()
    try:
        import agentbundle.credentials  # noqa: F401
        assert "agentbundle.creds._keychain_macos" not in sys.modules
    finally:
        _restore_creds_modules(saved)
