"""Public write API tests (spec task T8).

The write surface credential-setup migrates onto: keyring/dotfile/vault writes,
the `crypto_available`/`keyring_available` probes, and the keyring-first
`store_vault_master`. Sourcing/keyring paths are stdlib (tested without the
extra); the vault write is [crypto]-gated.
"""

from __future__ import annotations

import importlib.util
import os
import stat

import pytest

import credbroker
from credbroker import _core

_HAS_CRYPTO = (
    importlib.util.find_spec("cryptography") is not None
    and importlib.util.find_spec("argon2") is not None
)
requires_crypto = pytest.mark.skipif(not _HAS_CRYPTO, reason="requires the [crypto] extra")


class _FakeBackend:
    """Capturing keyring backend."""

    def __init__(self):
        self.written = {}

    def write_credential(self, namespace, key, value):
        self.written[(namespace, key)] = value

    def read_credential(self, namespace, key):
        return self.written.get((namespace, key))


@pytest.fixture
def home(tmp_path, monkeypatch):
    h = tmp_path / "home"
    (h / ".agentbundle").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(h))
    monkeypatch.setenv("USERPROFILE", str(h))
    monkeypatch.delenv(_core.VAULT_MASTER_ENV, raising=False)
    return h


def test_keyring_available_reflects_backend(monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", _FakeBackend())
    assert credbroker.keyring_available() is True
    monkeypatch.setattr(_core, "_tier2_backend", None)
    assert credbroker.keyring_available() is False


def test_store_in_keyring_writes_and_no_backend_raises(monkeypatch):
    fake = _FakeBackend()
    monkeypatch.setattr(_core, "_tier2_backend", fake)
    credbroker.store_in_keyring("jira", "API_TOKEN", "kr-secret")
    assert fake.written[("jira", "API_TOKEN")] == "kr-secret"

    monkeypatch.setattr(_core, "_tier2_backend", None)
    with pytest.raises(credbroker.Tier2HardFailError):
        credbroker.store_in_keyring("jira", "API_TOKEN", "x")


def test_store_in_dotfile_round_trips(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    credbroker.store_in_dotfile("jira", "API_TOKEN", "df-secret")
    creds = credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == "df-secret"


def test_crypto_available_matches_env():
    assert credbroker.crypto_available() is _HAS_CRYPTO


def test_store_vault_master_keyring_first(monkeypatch, home):
    # With a keyring, the master goes to the keyring — never to disk.
    fake = _FakeBackend()
    monkeypatch.setattr(_core, "_tier2_backend", fake)
    credbroker.store_vault_master("master-pw")
    assert fake.written[(_core._VAULT_MASTER_NAMESPACE, _core._VAULT_MASTER_KEY)] == "master-pw"
    assert not _core._vault_master_file().exists()  # nothing on disk
    assert credbroker.source_vault_master() == "master-pw"


def test_store_vault_master_file_when_no_keyring_is_0600(monkeypatch, home):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    credbroker.store_vault_master("master-pw")
    f = _core._vault_master_file()
    assert f.is_file()
    if os.name == "posix":
        assert stat.S_IMODE(f.stat().st_mode) == 0o600
    # Full round-trip: written file is re-sourced (and passes the read-side
    # reject-on-permissive check).
    assert credbroker.source_vault_master() == "master-pw"


@requires_crypto
def test_store_in_vault_round_trips(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    credbroker.store_in_vault("jira", "API_TOKEN", "vault-secret", master="master-pw")
    from credbroker import _vault

    assert _vault.read_credential("jira", "API_TOKEN", master="master-pw", path=_core._vault_path()) == "vault-secret"
