"""Vault master-secret sourcing + Tier-3 vault dispatch (spec task T5; AC6, AC5/AC7).

Two layers:
- Sourcing precedence (keyring -> env -> file, env before file) is stdlib and
  tested without the [crypto] extra by faking the Tier-2 backend.
- The Tier-3 dispatch in load_credentials (vault when present, fail-loud when
  unopenable) needs a real vault, so those tests are [crypto]-gated.
"""

from __future__ import annotations

import importlib.util
import os
import sys

import pytest

from credbroker import _core

_HAS_CRYPTO = (
    importlib.util.find_spec("cryptography") is not None
    and importlib.util.find_spec("argon2") is not None
)
requires_crypto = pytest.mark.skipif(not _HAS_CRYPTO, reason="requires the [crypto] extra")


class _FakeBackend:
    """Stand-in OS-keyring backend returning a master for the vault coordinates."""

    def __init__(self, master):
        self._master = master

    def read_credential(self, namespace, key):
        if (namespace, key) == (_core._VAULT_MASTER_NAMESPACE, _core._VAULT_MASTER_KEY):
            return self._master
        return None


@pytest.fixture
def home(tmp_path, monkeypatch):
    h = tmp_path / "home"
    (h / ".agentbundle").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(h))
    monkeypatch.setenv("USERPROFILE", str(h))
    monkeypatch.delenv(_core.VAULT_MASTER_ENV, raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    return h


def _master_file(home):
    return home / ".agentbundle" / "vault.master"


# ── sourcing precedence (stdlib; no [crypto] needed) ───────────────────


def test_keyring_wins_over_env_and_file(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", _FakeBackend("from-keyring"))
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "from-env")
    _master_file(home).write_text("from-file")
    assert _core._source_vault_master() == "from-keyring"


def test_env_used_when_no_keyring(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "from-env")
    assert _core._source_vault_master() == "from-env"


def test_file_used_when_no_keyring_no_env(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    f = _master_file(home)
    f.write_text("from-file\n")  # trailing newline tolerated
    if os.name == "posix":
        os.chmod(f, 0o600)
    assert _core._source_vault_master() == "from-file"


def test_permissive_master_file_refused(home, monkeypatch):
    if os.name != "posix":
        pytest.skip("POSIX mode check")
    monkeypatch.setattr(_core, "_tier2_backend", None)
    f = _master_file(home)
    f.write_text("from-file")
    os.chmod(f, 0o644)  # group/other-readable — the key to everything
    from credbroker import VaultUnavailableError

    with pytest.raises(VaultUnavailableError) as exc:
        _core._source_vault_master()
    assert "permissive" in str(exc.value)
    assert "from-file" not in str(exc.value)  # never embed the master value


def test_env_before_file_in_no_keyring_case(home, monkeypatch):
    # The signed-off precedence: env beats a stale on-disk file.
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "from-env")
    _master_file(home).write_text("from-file")
    assert _core._source_vault_master() == "from-env"


def test_none_when_no_source(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    assert _core._source_vault_master() is None


def test_keyring_miss_falls_through_to_env(home, monkeypatch):
    # Backend present but holds no master entry -> fall through to env.
    monkeypatch.setattr(_core, "_tier2_backend", _FakeBackend(None))
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "from-env")
    assert _core._source_vault_master() == "from-env"


# ── Tier-3 dispatch via load_credentials ([crypto]-gated) ──────────────


def _make_vault(master, namespace, key, value):
    from credbroker._vault import Vault

    v = Vault.create(master, path=_core._vault_path())
    v.set(namespace, key, value)
    v.save()


@requires_crypto
def test_load_credentials_reads_vault_via_env_master(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "master-pw")
    _make_vault("master-pw", "jira", "API_TOKEN", "vault-secret")
    import credbroker

    creds = credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == "vault-secret"


@requires_crypto
def test_vault_wins_over_plaintext_dotfile(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "master-pw")
    (home / ".agentbundle" / "credentials.env").write_text("JIRA_API_TOKEN=dotfile-secret\n")
    _make_vault("master-pw", "jira", "API_TOKEN", "vault-secret")
    import credbroker

    creds = credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == "vault-secret"


@requires_crypto
def test_vault_present_no_master_fails_loud(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    _make_vault("master-pw", "jira", "API_TOKEN", "v")  # vault exists, no master sourced
    import credbroker

    with pytest.raises(credbroker.VaultUnavailableError):
        credbroker.load_credentials("jira", required_keys=["API_TOKEN"])


@requires_crypto
def test_vault_present_crypto_missing_fails_loud(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "master-pw")
    _make_vault("master-pw", "jira", "API_TOKEN", "v")
    import credbroker

    # Simulate the [crypto] extra being absent at read time: clear both the
    # cached submodule and the bound package attribute, so `from . import _vault`
    # re-imports and fails (None in sys.modules raises ImportError).
    monkeypatch.delattr(credbroker, "_vault", raising=False)
    monkeypatch.setitem(sys.modules, "credbroker._vault", None)

    with pytest.raises(credbroker.VaultUnavailableError):
        credbroker.load_credentials("jira", required_keys=["API_TOKEN"])


@requires_crypto
def test_wrong_master_propagates_not_silent_miss(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    _make_vault("right-master", "jira", "API_TOKEN", "v")
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "wrong-master")
    import credbroker
    from credbroker._vault import VaultError

    # A wrong master must surface (VaultError), not degrade to "credential missing".
    with pytest.raises(VaultError):
        credbroker.load_credentials("jira", required_keys=["API_TOKEN"])


@requires_crypto
def test_vault_present_key_absent_is_clean_miss(home, monkeypatch):
    # A readable vault missing the requested key must surface as a clean miss
    # (CredentialsMissingError), NOT VaultUnavailableError and NOT a dotfile read
    # — a present vault must not turn "not configured yet" into a hard error.
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "master-pw")
    _make_vault("master-pw", "jira", "API_TOKEN", "vault-secret")
    import credbroker

    with pytest.raises(credbroker.CredentialsMissingError):
        credbroker.load_credentials("jira", required_keys=["NOT_IN_VAULT"])


@requires_crypto
def test_ac6_credbroker_exports_no_env(home, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "master-pw")
    _make_vault("master-pw", "jira", "API_TOKEN", "vault-secret")
    import credbroker

    before = dict(os.environ)
    credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert dict(os.environ) == before  # no env var added/changed by credbroker


def test_no_vault_falls_to_dotfile_floor(home, monkeypatch):
    # Clean degrade (no vault): the plaintext dotfile remains the floor.
    monkeypatch.setattr(_core, "_tier2_backend", None)
    (home / ".agentbundle" / "credentials.env").write_text("JIRA_API_TOKEN=dotfile-secret\n")
    import credbroker

    creds = credbroker.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == "dotfile-secret"
