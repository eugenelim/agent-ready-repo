"""T5: Windows Credential Manager Tier-2 backend — Windows-only round-trip.

Gated on ``sys.platform == "win32"`` because ``ctypes.WinDLL`` only
exists on Windows. The pure-logic tests
(``tests/unit/test_credman_windows_logic.py``) cover struct shape,
constants, target-name format, and the error classifier on every
platform — those run on Darwin / Linux CI even though no real
Credential Manager is present.

CI matrix note: this repo's current build-check workflow does not
include a ``windows-latest`` runner; this test will be exercised when
that matrix lands (tracked as a follow-up to spec § AC10). Locally on
a Windows dev box, ``pytest packages/agentbundle/tests/integration/test_credman_windows.py``
will run.
"""

from __future__ import annotations

import os
import sys

import pytest


pytestmark = pytest.mark.skipif(
    sys.platform != "win32",
    reason="Windows Credential Manager backend — Windows-only",
)


@pytest.fixture
def backend(tmp_path, monkeypatch):
    """Scope target-name prefix to a ``tmp_path`` hash so test entries
    can't collide with real ``agentbundle:`` entries in the developer's
    Credential Manager (spec § AC35 / plan T5 § Test isolation)."""
    from agentbundle.creds import _credman_windows as cm
    unique = f"agentbundle-test-{abs(hash(str(tmp_path))) & 0xffffffff:08x}"
    monkeypatch.setattr(cm, "SERVICE_PREFIX_OVERRIDE", unique)

    written: list[tuple[str, str]] = []
    real_write = cm.write_credential

    def tracking_write(namespace, key, value):
        written.append((namespace, key))
        return real_write(namespace, key, value)

    monkeypatch.setattr(cm, "write_credential", tracking_write)
    yield cm
    for namespace, key in written:
        try:
            cm.delete_credential(namespace, key)
        except Exception:
            pass


def test_round_trip_byte_equality(backend):
    """AC10: write a value, read it, ``assert read_back == value`` (the
    UTF-16-LE encoding round-trips through ``CredentialBlob``)."""
    token = "round-trip-tok-1"
    backend.write_credential("fixture_t5", "API_TOKEN", token)
    assert backend.read_credential("fixture_t5", "API_TOKEN") == token


def test_unicode_round_trip(backend):
    """AC10: non-ASCII values round-trip cleanly via UTF-16-LE."""
    token = "unicode-tok-ünïcödé-π-字"
    backend.write_credential("fixture_t5", "API_TOKEN", token)
    assert backend.read_credential("fixture_t5", "API_TOKEN") == token


def test_missing_credential_returns_none(backend):
    """AC11: ``ERROR_NOT_FOUND`` (1168) → ``None`` so the resolver falls
    through to Tier 3."""
    assert backend.read_credential("fixture_t5_never_set", "API_TOKEN") is None


def test_upsert_replaces_value(backend):
    """A second write to the same target replaces the value
    (Credential Manager's default semantics for ``CredWriteW``)."""
    backend.write_credential("fixture_t5", "API_TOKEN", "first")
    backend.write_credential("fixture_t5", "API_TOKEN", "second")
    assert backend.read_credential("fixture_t5", "API_TOKEN") == "second"


def test_multiple_keys_per_namespace_round_trip(backend):
    backend.write_credential("fixture_t5", "API_TOKEN", "tok")
    backend.write_credential("fixture_t5", "BASE_URL", "https://x.test")
    assert backend.read_credential("fixture_t5", "API_TOKEN") == "tok"
    assert backend.read_credential("fixture_t5", "BASE_URL") == "https://x.test"


def test_delete_removes_entry(backend):
    backend.write_credential("fixture_t5", "API_TOKEN", "secret")
    backend.delete_credential("fixture_t5", "API_TOKEN")
    assert backend.read_credential("fixture_t5", "API_TOKEN") is None


def test_delete_missing_is_idempotent(backend):
    """``ERROR_NOT_FOUND`` on delete is swallowed (idempotent)."""
    backend.delete_credential("fixture_t5_never_set", "API_TOKEN")


def test_credential_metadata_after_write(backend):
    """AC9: after write, the stored credential carries the expected
    ``TargetName``, ``UserName``, ``Type``, ``Persist`` values.

    We re-read via ``CredReadW`` and inspect the returned struct's
    fields (using ``ctypes.string_at`` for the blob copy on read).
    """
    import ctypes
    from ctypes import POINTER, byref
    backend.write_credential("fixture_t5_meta", "API_TOKEN", "secret")
    out_ptr = POINTER(backend.CREDENTIAL)()
    target = backend._target_name("fixture_t5_meta", "API_TOKEN")
    ok = backend._advapi32.CredReadW(
        target, backend.CRED_TYPE_GENERIC, 0, byref(out_ptr)
    )
    assert ok
    try:
        cred = out_ptr.contents
        assert cred.TargetName == target
        assert cred.UserName == "fixture_t5_meta"
        assert cred.Type == backend.CRED_TYPE_GENERIC
        assert cred.Persist == backend.CRED_PERSIST_LOCAL_MACHINE
    finally:
        backend._advapi32.CredFree(out_ptr)
