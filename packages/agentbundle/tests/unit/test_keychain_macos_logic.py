"""macOS Keychain Tier-2 backend — pure-logic tests (spec § AC22).

Parallel in shape to ``test_credman_windows_logic.py``: covers the
exit-code classifier matrix and the account-label format on every
platform. The actual ``security`` subprocess round-trip is exercised
on the developer's macOS box via ``tests/integration/test_keychain_macos.py``
(gated on ``sys.platform == "darwin"``).
"""

from __future__ import annotations

import pytest

from agentbundle.creds import _keychain_macos as km
from agentbundle.creds.exceptions import Tier2HardFailError


def test_account_label_format():
    """AC6: account label is ``<namespace>:<key>``."""
    assert km._account("jira", "API_TOKEN") == "jira:API_TOKEN"
    assert km._account("ns", "K") == "ns:K"


def test_classify_zero_returns_none():
    """Success — caller treats ``None`` as "no error to embed"."""
    assert km._classify_macos_exit_code(0, "read") is None


def test_classify_not_found_returns_none():
    """AC22: ``44`` (errSecItemNotFound) is a legitimate miss; caller
    short-circuits before calling the classifier in read/delete paths,
    but the classifier itself also returns ``None`` so a defensive call
    doesn't spuriously raise."""
    assert km._classify_macos_exit_code(km.EXIT_NOT_FOUND, "read") is None


def test_classify_interaction_not_allowed_names_symbolic():
    """AC22: ``25308`` (errSecInteractionNotAllowed) — Keychain locked.
    The classifier returns a symbolic name string so the
    ``Tier2HardFailError`` message embeds it.
    """
    msg = km._classify_macos_exit_code(km.EXIT_INTERACTION_NOT_ALLOWED, "read")
    assert msg is not None
    assert "errSecInteractionNotAllowed" in msg
    assert "25308" in msg


def test_classify_not_available_names_symbolic():
    """AC22: ``-25291`` (errSecNotAvailable) — Keychain service unavailable."""
    msg = km._classify_macos_exit_code(km.EXIT_NOT_AVAILABLE, "write")
    assert msg is not None
    assert "errSecNotAvailable" in msg
    assert "-25291" in msg


def test_classify_duplicate_item_names_symbolic():
    """AC22: ``45`` (errSecDuplicateItem) — defensive; ``-U`` upsert
    means the write path should never surface this, but a future argv
    change dropping ``-U`` produces a readable error."""
    msg = km._classify_macos_exit_code(km.EXIT_DUPLICATE_ITEM, "write")
    assert msg is not None
    assert "errSecDuplicateItem" in msg
    assert "45" in msg


def test_classify_unknown_code_falls_back_to_raw():
    """Defensive: any uncategorised non-zero rc surfaces as a hard fail
    naming the raw exit code rather than ``None`` (silent miss)."""
    msg = km._classify_macos_exit_code(9999, "read")
    assert msg is not None
    assert "9999" in msg


@pytest.mark.parametrize(
    "rc, expected_symbol",
    [
        (km.EXIT_INTERACTION_NOT_ALLOWED, "errSecInteractionNotAllowed"),
        (km.EXIT_NOT_AVAILABLE, "errSecNotAvailable"),
        (km.EXIT_DUPLICATE_ITEM, "errSecDuplicateItem"),
    ],
)
def test_classify_matrix(rc, expected_symbol):
    """Parametric pin on the AC22 matrix — one row per known code."""
    msg = km._classify_macos_exit_code(rc, "read")
    assert msg is not None
    assert expected_symbol in msg


def test_write_credential_embeds_symbolic_name_on_hard_fail(monkeypatch):
    """Integration of classifier with ``write_credential``: a non-zero
    ``security`` exit must produce a ``Tier2HardFailError`` whose
    message embeds the symbolic name (not just the raw rc).

    Fakes ``subprocess.Popen`` so this test runs on every platform.
    """
    class FakeProc:
        returncode = km.EXIT_INTERACTION_NOT_ALLOWED

        def communicate(self, input=None):
            return (b"", b"User interaction is not allowed.")

    monkeypatch.setattr(
        "subprocess.Popen",
        lambda *a, **kw: FakeProc(),
    )
    with pytest.raises(Tier2HardFailError) as excinfo:
        km.write_credential("jira", "API_TOKEN", "tok-abc")
    assert "errSecInteractionNotAllowed" in str(excinfo.value)
    assert "25308" in str(excinfo.value)


def test_read_credential_embeds_symbolic_name_on_hard_fail(monkeypatch):
    """Integration of classifier with ``read_credential``: a non-zero,
    non-``EXIT_NOT_FOUND`` exit produces a ``Tier2HardFailError``
    embedding the symbolic name.
    """
    class FakeResult:
        returncode = km.EXIT_NOT_AVAILABLE
        stdout = ""
        stderr = "Keychain not available"

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: FakeResult(),
    )
    with pytest.raises(Tier2HardFailError) as excinfo:
        km.read_credential("jira", "API_TOKEN")
    assert "errSecNotAvailable" in str(excinfo.value)
    assert "-25291" in str(excinfo.value)


def test_read_credential_returns_none_on_not_found(monkeypatch):
    """AC22: ``EXIT_NOT_FOUND`` falls through to Tier 3 — caller sees
    ``None``, no exception."""
    class FakeResult:
        returncode = km.EXIT_NOT_FOUND
        stdout = ""
        stderr = "The specified item could not be found in the keychain."

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **kw: FakeResult(),
    )
    assert km.read_credential("jira", "API_TOKEN") is None
