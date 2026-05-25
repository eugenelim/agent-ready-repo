"""T5 — pure-logic tests for the Windows Credential Manager backend.

These tests inspect struct shapes, target-name formatting, and the
error-code classifier WITHOUT calling the real Win32 API. They run on
every platform so the structure / classifier contracts are exercised
on Darwin + Linux CI even though no end-to-end Credential Manager
round-trip is possible there.

The actual API tests (``test_credman_windows.py``) gate on
``sys.platform == "win32"``.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt

import pytest

from agentbundle.creds import _credman_windows as cm
from agentbundle.creds.exceptions import Tier2HardFailError


def test_credential_struct_field_order_matches_wincred_h():
    """AC9: field order must match the Win32 ``CREDENTIAL`` ABI.

    Wrong-order or wrong-sized fields don't raise — they return
    garbage on real Win32. Pinning the field order in a test is the
    only catch-net.
    """
    names = [name for name, _typ in cm.CREDENTIAL._fields_]
    assert names == [
        "Flags",
        "Type",
        "TargetName",
        "Comment",
        "LastWritten",
        "CredentialBlobSize",
        "CredentialBlob",
        "Persist",
        "AttributeCount",
        "Attributes",
        "TargetAlias",
        "UserName",
    ]


def test_credential_struct_field_types():
    """AC9: each field is the correct ctypes wintypes alias."""
    fields = dict(cm.CREDENTIAL._fields_)
    assert fields["Flags"] is wt.DWORD
    assert fields["Type"] is wt.DWORD
    assert fields["TargetName"] is wt.LPWSTR
    assert fields["Comment"] is wt.LPWSTR
    assert fields["LastWritten"] is wt.FILETIME
    assert fields["CredentialBlobSize"] is wt.DWORD
    assert fields["Persist"] is wt.DWORD
    assert fields["AttributeCount"] is wt.DWORD
    assert fields["Attributes"] is ctypes.c_void_p
    assert fields["TargetAlias"] is wt.LPWSTR
    assert fields["UserName"] is wt.LPWSTR


def test_credential_zero_initialised_defaults():
    """AC9: ``CREDENTIAL()`` zero-inits every field — required by
    ``CRED_TYPE_GENERIC`` (Flags must be 0; Attributes NULL when
    AttributeCount==0)."""
    cred = cm.CREDENTIAL()
    assert cred.Flags == 0
    assert cred.Type == 0  # caller sets to CRED_TYPE_GENERIC explicitly
    assert cred.TargetName is None
    assert cred.Comment is None
    # FILETIME is a struct with dwLowDateTime/dwHighDateTime — both zero.
    assert cred.LastWritten.dwLowDateTime == 0
    assert cred.LastWritten.dwHighDateTime == 0
    assert cred.CredentialBlobSize == 0
    assert not cred.CredentialBlob  # NULL pointer
    assert cred.Persist == 0
    assert cred.AttributeCount == 0
    assert cred.Attributes in (None, 0)  # c_void_p NULL
    assert cred.TargetAlias is None
    assert cred.UserName is None


def test_constants_match_wincred_h():
    """AC9: numeric constants match the Win32 header values."""
    assert cm.CRED_TYPE_GENERIC == 1
    assert cm.CRED_PERSIST_LOCAL_MACHINE == 2


def test_error_code_constants_match_winerror_h():
    """AC11: numeric error codes match the Win32 header values."""
    assert cm.ERROR_NOT_FOUND == 1168
    assert cm.ERROR_NO_SUCH_LOGON_SESSION == 1312
    assert cm.ERROR_INVALID_FLAGS == 1004
    assert cm.ERROR_LOGON_FAILURE == 1326


def test_target_name_format():
    """AC9: ``TargetName == "agentbundle:<namespace>:<key>"``."""
    assert cm._target_name("jira", "API_TOKEN") == "agentbundle:jira:API_TOKEN"
    assert cm._target_name("ns", "K") == "agentbundle:ns:K"


def test_target_name_honours_service_prefix_override(monkeypatch):
    """AC35 test-isolation: tests can scope the target-name prefix to a
    ``tmp_path``-derived unique value."""
    monkeypatch.setattr(cm, "SERVICE_PREFIX_OVERRIDE", "agentbundle-test-abcd1234")
    assert (
        cm._target_name("jira", "API_TOKEN")
        == "agentbundle-test-abcd1234:jira:API_TOKEN"
    )


def test_classify_last_error_no_such_logon_session_raises():
    """AC11: ERROR_NO_SUCH_LOGON_SESSION (1312) raises ``Tier2HardFailError``.

    Resolver MUST NOT fall through to Tier 3 — silent degradation
    defeats the security posture the user chose.
    """
    with pytest.raises(Tier2HardFailError, match="1312"):
        cm._classify_last_error(cm.ERROR_NO_SUCH_LOGON_SESSION, "read")


def test_classify_last_error_invalid_flags_raises():
    """AC11: ERROR_INVALID_FLAGS (1004) raises ``Tier2HardFailError``."""
    with pytest.raises(Tier2HardFailError, match="1004"):
        cm._classify_last_error(cm.ERROR_INVALID_FLAGS, "write")


def test_classify_last_error_logon_failure_raises():
    """AC11: ERROR_LOGON_FAILURE (1326) raises ``Tier2HardFailError``
    naming DPAPI key-derivation failure."""
    with pytest.raises(Tier2HardFailError, match="1326"):
        cm._classify_last_error(cm.ERROR_LOGON_FAILURE, "read")


def test_classify_last_error_unknown_code_raises():
    """Defensive: any uncategorised non-zero rc surfaces as a hard fail
    rather than silently degrading."""
    with pytest.raises(Tier2HardFailError, match="unexpected"):
        cm._classify_last_error(9999, "read")


def test_blob_round_trip_via_utf16le():
    """AC10 inverse: the encoding round-trip (without calling Win32)
    matches the wire format the spec mandates — UTF-16-LE byte
    sequence equals what ``decode("utf-16-le")`` reverses."""
    token = "tok-abc-ünïcödé"
    blob = token.encode("utf-16-le")
    # Each UTF-16 code unit is 2 bytes; LE means low byte first.
    assert len(blob) == 2 * len(token)
    assert blob[0:2] == b"t\x00"
    # Round-trip:
    assert blob.decode("utf-16-le") == token
