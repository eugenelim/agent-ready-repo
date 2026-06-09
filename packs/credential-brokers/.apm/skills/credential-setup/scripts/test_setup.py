"""credential-setup tests (spec task T8) — credential-setup ships none today.

Exercises the three Tier-selection orchestration paths after the migration onto
credbroker's public write API, plus the import-surface invariant (no
credentials_shim, no underscore-prefixed credbroker name). Run as:
``python -m pytest test_setup.py`` from this directory (credbroker installed).
"""

from __future__ import annotations

import ast
import importlib.util
import os
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import setup  # noqa: E402

from credbroker import _core  # noqa: E402

_HAS_CRYPTO = (
    importlib.util.find_spec("cryptography") is not None
    and importlib.util.find_spec("argon2") is not None
)
requires_crypto = pytest.mark.skipif(not _HAS_CRYPTO, reason="requires the [crypto] extra")

SECRET = "tok-secret-value"


class _FakeBackend:
    def __init__(self):
        self.written = {}

    def write_credential(self, namespace, key, value):
        self.written[(namespace, key)] = value

    def read_credential(self, namespace, key):
        return self.written.get((namespace, key))


def _schema_file(tmp_path):
    p = tmp_path / "creds-schema.toml"
    p.write_text(
        '[namespace]\nname = "jira"\n\n'
        '[[namespace.keys]]\nname = "API_TOKEN"\nlabel = "Jira API token"\nsecret = true\n',
        encoding="utf-8",
    )
    return p


@pytest.fixture
def env(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".agentbundle").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.delenv(_core.VAULT_MASTER_ENV, raising=False)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    # Bypass interactive value entry; the orchestration under test is tier
    # selection + write, not the prompt loop.
    monkeypatch.setattr(setup, "_prompt", lambda schema: {"API_TOKEN": SECRET})
    return home


def _run(tmp_path, *flags):
    return setup.main([*flags, "jira", "--schema-path", str(_schema_file(tmp_path))])


def test_keyring_path(env, tmp_path, monkeypatch):
    fake = _FakeBackend()
    monkeypatch.setattr(_core, "_tier2_backend", fake)
    rc = _run(tmp_path)
    assert rc == 0
    assert fake.written[("jira", "API_TOKEN")] == SECRET


@requires_crypto
def test_no_keyring_crypto_vault_master_from_env(env, tmp_path, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "master-pw")
    rc = _run(tmp_path)
    assert rc == 0
    from credbroker import _vault

    assert _vault.read_credential("jira", "API_TOKEN", master="master-pw", path=_core._vault_path()) == SECRET


@requires_crypto
def test_no_keyring_crypto_prompts_and_establishes_master(env, tmp_path, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    # No master sourceable -> _write_tier3 prompts via getpass; mock it.
    monkeypatch.setattr(setup.getpass, "getpass", lambda *a, **k: "freshly-set-master")
    rc = _run(tmp_path)
    assert rc == 0
    # The master was established on disk at 0600, and the value is in the vault.
    mf = _core._vault_master_file()
    assert mf.is_file()
    if os.name == "posix":
        assert (mf.stat().st_mode & 0o077) == 0  # not group/other accessible
    from credbroker import _vault

    assert _vault.read_credential("jira", "API_TOKEN", master="freshly-set-master", path=_core._vault_path()) == SECRET


@requires_crypto
def test_wrong_master_against_existing_vault_exits_3_not_traceback(env, tmp_path, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    from credbroker import _vault

    v = _vault.Vault.create("right-master", path=_core._vault_path())
    v.set("jira", "API_TOKEN", "old")
    v.save()
    # A wrong sourced master must fail cleanly (exit 3), not dump a traceback.
    monkeypatch.setenv(_core.VAULT_MASTER_ENV, "wrong-master")
    assert _run(tmp_path) == 3


@requires_crypto
def test_permissive_master_file_exits_3(env, tmp_path, monkeypatch):
    if os.name != "posix":
        pytest.skip("POSIX mode check")
    monkeypatch.setattr(_core, "_tier2_backend", None)
    mf = _core._vault_master_file()
    mf.write_text("some-master")
    os.chmod(mf, 0o644)  # group/other-readable -> source rejects -> clean exit 3
    assert _run(tmp_path) == 3


def test_no_keyring_no_crypto_falls_to_dotfile(env, tmp_path, monkeypatch):
    monkeypatch.setattr(_core, "_tier2_backend", None)
    monkeypatch.setattr(setup, "crypto_available", lambda: False)  # simulate no [crypto]
    rc = _run(tmp_path)
    assert rc == 0
    creds = _core.load_credentials("jira", required_keys=["API_TOKEN"])
    assert creds.API_TOKEN == SECRET


def test_setup_imports_credbroker_not_shim_nor_private():
    src = pathlib.Path(setup.__file__).read_text()
    tree = ast.parse(src)
    target = "credentials" + "_shim"
    imported_credbroker = False
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module != target, "setup.py must not import the shim"
            if (node.module or "").split(".")[0] == "credbroker":
                imported_credbroker = True
                for alias in node.names:
                    assert not alias.name.startswith("_"), f"private credbroker import: {alias.name}"
    assert imported_credbroker, "setup.py must import from credbroker"
