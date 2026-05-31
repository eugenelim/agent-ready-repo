"""Windows Credential Manager Tier-2 backend.

In-process ``ctypes`` against ``advapi32.dll``'s ``CredReadW`` /
``CredWriteW`` / ``CredDeleteW`` / ``CredFree`` — stdlib only, no
``pywin32`` dependency. Token bytes never cross a process boundary;
the entire flow stays inside the Python heap.

Struct layout: per ``wincred.h``, ``CREDENTIAL`` carries 12 fields.
For a generic password the load-bearing ones are ``TargetName``,
``UserName``, ``CredentialBlob`` / ``CredentialBlobSize``, ``Type``
and ``Persist``; the rest (``Flags``, ``Comment``, ``LastWritten``,
``AttributeCount``, ``Attributes``, ``TargetAlias``) are
zero-initialised via ``ctypes.Structure`` defaults — required by
``CRED_TYPE_GENERIC`` (``Flags`` must be 0; ``Attributes`` must be
NULL when ``AttributeCount`` is 0; ``LastWritten`` is set by the API
and ignored on write).

The loader imports this module **only** when
``sys.platform == "win32"``. The advapi32 binding is platform-guarded
below so the module itself stays importable on every platform; tests
that don't actually call the OS can construct ``CREDENTIAL`` instances
and exercise the helpers without a real Windows host.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wt
import sys
from ctypes import POINTER, Structure, byref

from .credentials_shim import Tier2HardFailError

# Constants from ``wincred.h``:
CRED_TYPE_GENERIC = 1
CRED_PERSIST_LOCAL_MACHINE = 2

# Win32 error codes — sourced from ``winerror.h``:
ERROR_NOT_FOUND = 1168          # falls through to Tier 3
ERROR_NO_SUCH_LOGON_SESSION = 1312
ERROR_INVALID_FLAGS = 1004
ERROR_LOGON_FAILURE = 1326

TARGET_PREFIX = "agentbundle"
# Tests can monkeypatch this to a ``tmp_path``-derived value so test
# target-names can't collide with the developer's real Credential
# Manager entries.
SERVICE_PREFIX_OVERRIDE: str | None = None


class CREDENTIAL(Structure):
    """Mirror of the Win32 ``CREDENTIAL`` struct (wincred.h, ``CredW``).

    Field order and types must match the Win32 ABI exactly — a wrong-
    sized field on Windows returns garbage rather than raising, which
    is why a byte-equality round-trip test covers every field.
    """

    _fields_ = [
        ("Flags", wt.DWORD),
        ("Type", wt.DWORD),
        ("TargetName", wt.LPWSTR),
        ("Comment", wt.LPWSTR),
        ("LastWritten", wt.FILETIME),
        ("CredentialBlobSize", wt.DWORD),
        ("CredentialBlob", POINTER(wt.BYTE)),
        ("Persist", wt.DWORD),
        ("AttributeCount", wt.DWORD),
        ("Attributes", ctypes.c_void_p),
        ("TargetAlias", wt.LPWSTR),
        ("UserName", wt.LPWSTR),
    ]


def _bind_advapi32():
    """Bind the four ``advapi32.dll`` entry points used by this backend.

    Pinned to a single function so tests that don't need the real DLL
    (struct shape, target-name format, error classifier) can run on
    any platform.
    """
    advapi32 = ctypes.WinDLL("advapi32", use_last_error=True)  # type: ignore[attr-defined]
    advapi32.CredReadW.restype = wt.BOOL
    advapi32.CredReadW.argtypes = [
        wt.LPCWSTR, wt.DWORD, wt.DWORD, POINTER(POINTER(CREDENTIAL))
    ]
    advapi32.CredWriteW.restype = wt.BOOL
    advapi32.CredWriteW.argtypes = [POINTER(CREDENTIAL), wt.DWORD]
    advapi32.CredDeleteW.restype = wt.BOOL
    advapi32.CredDeleteW.argtypes = [wt.LPCWSTR, wt.DWORD, wt.DWORD]
    advapi32.CredFree.restype = None
    advapi32.CredFree.argtypes = [ctypes.c_void_p]
    return advapi32


# Platform-guarded binding. ``ctypes.WinDLL`` only exists on Windows;
# importing this module on non-Windows leaves ``_advapi32`` as ``None``
# so test files can still inspect struct shape + helpers without the
# DLL present.
if sys.platform == "win32":  # pragma: no cover — only exercised on Windows
    _advapi32 = _bind_advapi32()
else:
    _advapi32 = None


def _target_name(namespace: str, key: str) -> str:
    """Compose the Win32 ``TargetName``."""
    prefix = SERVICE_PREFIX_OVERRIDE or TARGET_PREFIX
    return f"{prefix}:{namespace}:{key}"


def _classify_last_error(rc: int, op: str) -> None:
    """Map the Win32 last-error code to the dispatch matrix.

    ``ERROR_NOT_FOUND`` is the caller's responsibility (it indicates a
    legitimate miss — caller returns ``None``). Every other code on
    this matrix raises ``Tier2HardFailError`` so the resolver does not
    silently degrade to Tier 3.
    """
    if rc == ERROR_NO_SUCH_LOGON_SESSION:
        raise Tier2HardFailError(
            f"Windows Credential Manager {op} failed: "
            f"ERROR_NO_SUCH_LOGON_SESSION (1312) — no logon session "
            f"(running under LocalSystem or similar service context)"
        )
    if rc == ERROR_INVALID_FLAGS:
        raise Tier2HardFailError(
            f"Windows Credential Manager {op} failed: "
            f"ERROR_INVALID_FLAGS (1004) — invalid flag value"
        )
    if rc == ERROR_LOGON_FAILURE:
        raise Tier2HardFailError(
            f"Windows Credential Manager {op} failed: "
            f"ERROR_LOGON_FAILURE (1326) — DPAPI key-derivation failure"
        )
    raise Tier2HardFailError(
        f"Windows Credential Manager {op} failed: "
        f"unexpected Win32 error code {rc}"
    )


def read_credential(namespace: str, key: str) -> str | None:
    """Read ``(namespace, key)`` from Credential Manager.

    Returns ``None`` on ``ERROR_NOT_FOUND`` (resolver falls through to
    Tier 3); raises ``Tier2HardFailError`` on every other documented
    failure.
    """
    target = _target_name(namespace, key)
    out_ptr = POINTER(CREDENTIAL)()
    ok = _advapi32.CredReadW(target, CRED_TYPE_GENERIC, 0, byref(out_ptr))
    if not ok:
        rc = ctypes.get_last_error()
        if rc == ERROR_NOT_FOUND:
            return None
        _classify_last_error(rc, "read")
        return None  # unreachable — _classify always raises
    try:
        cred = out_ptr.contents
        size = int(cred.CredentialBlobSize)
        if size == 0 or not cred.CredentialBlob:
            return ""
        # Copy ``size`` bytes from the blob pointer; the token is stored
        # as UTF-16-LE (matches the encoding used on write).
        blob_bytes = ctypes.string_at(cred.CredentialBlob, size)
        return blob_bytes.decode("utf-16-le")
    finally:
        _advapi32.CredFree(out_ptr)


def write_credential(namespace: str, key: str, value: str) -> None:
    """Write ``value`` to ``(namespace, key)``.

    The token is UTF-16-LE encoded and stored in a writable buffer
    pointed to by ``CredentialBlob``; ``CredentialBlobSize`` is the
    byte length of that buffer. The token never leaves the Python heap.
    """
    target = _target_name(namespace, key)
    blob = value.encode("utf-16-le")
    blob_buf = ctypes.create_string_buffer(blob, len(blob))

    cred = CREDENTIAL()
    # All other fields stay at ctypes.Structure's zero-init defaults
    # (Flags=0, Comment=None, LastWritten=FILETIME(0,0),
    # AttributeCount=0, Attributes=None, TargetAlias=None) — required
    # by CRED_TYPE_GENERIC.
    cred.Type = CRED_TYPE_GENERIC
    cred.TargetName = target
    cred.CredentialBlobSize = len(blob)
    cred.CredentialBlob = ctypes.cast(blob_buf, POINTER(wt.BYTE))
    cred.Persist = CRED_PERSIST_LOCAL_MACHINE
    cred.UserName = namespace

    ok = _advapi32.CredWriteW(byref(cred), 0)
    if not ok:
        rc = ctypes.get_last_error()
        _classify_last_error(rc, "write")


def delete_credential(namespace: str, key: str) -> None:
    """Idempotent delete — ``ERROR_NOT_FOUND`` is swallowed."""
    target = _target_name(namespace, key)
    ok = _advapi32.CredDeleteW(target, CRED_TYPE_GENERIC, 0)
    if not ok:
        rc = ctypes.get_last_error()
        if rc == ERROR_NOT_FOUND:
            return
        _classify_last_error(rc, "delete")
