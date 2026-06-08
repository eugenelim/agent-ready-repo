"""Graceful-degrade matrix (spec task T6; AC7, AC13).

Drives ``load_credentials`` across the ``[crypto] × keyring`` environment cells
and asserts the resolved tier + no-leak per cell. The matrix is the resilience
contract: every cell resolves (or cleanly floors) without a crash or import
error, and no resolved value leaks via the ``Credentials`` repr.

| crypto | keyring | vault | resolves via                    |
|--------|---------|-------|---------------------------------|
| yes    | yes     | yes   | vault (master from keyring)     | cell A
| yes    | no      | yes   | vault (master from env)         | cell B
| n/a    | yes     | no    | keyring (Tier 2)                | cell C
| n/a    | no      | no    | plaintext dotfile floor (Tier 3)| cell D

The ``[crypto] absent`` clean-degrade is the no-vault row (an adopter who can't
install the extra has no encrypted vault): resolution is identical with or
without cryptography because Tier 3 never imports ``_vault`` absent a vault
file. The crash-class ``[crypto] absent + vault present → VaultUnavailableError``
fail-loud path is pinned in test_master_sourcing (T5), not here.
"""

from __future__ import annotations

import importlib.util
import os

import pytest

from credbroker import _core

_HAS_CRYPTO = (
    importlib.util.find_spec("cryptography") is not None
    and importlib.util.find_spec("argon2") is not None
)
requires_crypto = pytest.mark.skipif(not _HAS_CRYPTO, reason="requires the [crypto] extra")

SECRET = "tier-secret-must-not-leak"


class _FakeBackend:
    """Fake OS keyring: returns whatever (namespace, key) pairs it's seeded with."""

    def __init__(self, entries):
        self._entries = entries

    def read_credential(self, namespace, key):
        return self._entries.get((namespace, key))


@pytest.fixture
def home(tmp_path, monkeypatch):
    h = tmp_path / "home"
    (h / ".agentbundle").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(h))
    monkeypatch.setenv("USERPROFILE", str(h))
    monkeypatch.delenv(_core.VAULT_MASTER_ENV, raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    return h


def _make_vault(master, namespace, key, value):
    from credbroker._vault import Vault

    v = Vault.create(master, path=_core._vault_path())
    v.set(namespace, key, value)
    v.save()


def _assert_no_leak(creds):
    assert SECRET not in repr(creds)


# ── cell A: crypto + keyring + vault → vault (master from keyring) ──────


@requires_crypto
def test_cell_a_crypto_keyring_vault(home, monkeypatch):
    # Keyring holds the vault master but not the credential itself; Tier 2 misses
    # the credential, Tier 3 opens the vault using the keyring-held master.
    monkeypatch.setattr(
        _core, "_tier2_backend",
        _FakeBackend({(_core._VAULT_MASTER_NAMESPACE, _core._VAULT_MASTER_KEY): "master-pw"}),
    )
    _make_vault("master-pw", "jira", "API_TOKEN", SECRET)
    import credbroker

    creds = credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == SECRET
    _assert_no_leak(creds)


# ── cell B: crypto + no keyring + vault → vault (master from env) ───────


@requires_crypto
def test_cell_b_crypto_nokeyring_vault(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "master-pw")
    _make_vault("master-pw", "jira", "API_TOKEN", SECRET)
    import credbroker

    creds = credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == SECRET
    _assert_no_leak(creds)


# ── cell C: keyring + no vault → keyring (Tier 2), no crash without crypto ──


def test_cell_c_keyring_novault(home, monkeypatch):
    # Keyring resolves the credential directly at Tier 2; no vault file exists,
    # so Tier 3 / _vault is never reached — resolution is crypto-independent.
    monkeypatch.setattr(
        _core, "_tier2_backend",
        _FakeBackend({("jira", "API_TOKEN"): SECRET}),
    )
    import credbroker

    creds = credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == SECRET
    _assert_no_leak(creds)


# ── cell D: no keyring + no vault → plaintext dotfile floor (Tier 3) ────


def test_cell_d_nokeyring_novault_dotfile_floor(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    (home / ".agentbundle" / "credentials.env").write_text(
        f"JIRA_API_TOKEN={SECRET}\n", encoding="utf-8"
    )
    import credbroker

    creds = credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == SECRET
    _assert_no_leak(creds)


def test_cell_d_both_absent_nothing_configured_is_clean_miss(home, monkeypatch):
    # Both tiers absent and nothing in the dotfile: a clean CredentialsMissingError
    # (the floor still works — no crash, no import error), and the error names the
    # namespace/key but never a value.
    monkeypatch.setattr(_core, "_tier2_backend", None)
    import credbroker

    with pytest.raises(credbroker.CredentialsMissingError) as exc:
        credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert "jira" in str(exc.value) and "API_TOKEN" in str(exc.value)


@requires_crypto
def test_failure_path_no_leak_with_secret_present(home, monkeypatch, capsys):
    # A failure path *with a secret configured*: the vault holds SECRET but the
    # sourced master is wrong -> VaultError. The secret must not surface in the
    # exception message or on stdout/stderr (AC13's failure-path no-leak, at
    # integration altitude — the other cells configure no secret on their miss).
    monkeypatch.setattr(_core, "_tier2_backend", None)
    _make_vault("right-master", "jira", "API_TOKEN", SECRET)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "wrong-master")
    import credbroker
    from credbroker._vault import VaultError

    with pytest.raises(VaultError) as exc:
        credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert SECRET not in str(exc.value)
    captured = capsys.readouterr()
    assert SECRET not in captured.out and SECRET not in captured.err


def test_cell_d_env_tier1_floor_without_any_deps(home, monkeypatch):
    # The pip-free floor: env Tier-1 resolves with no keyring, no vault, no dotfile.
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv("JIRA_API_TOKEN", SECRET)
    import credbroker

    creds = credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == SECRET
    _assert_no_leak(creds)
